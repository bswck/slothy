#!/usr/bin/env bash
# (C) 2023–present Bartosz Sławecki (bswck)
#
# Interact with bswck/skeleton (current version: https://github.com/bswck/skeleton/tree/0.0.2rc-62-g52ffbf3).
#
# This file was generated from bswck/skeleton@0.0.2rc-62-g52ffbf3.
# Instead of changing this particular file, you might want to alter the template:
# https://github.com/bswck/skeleton/tree/0.0.2rc-62-g52ffbf3/project/scripts/skeleton.%7B%7Bsref%7D%7D.bash.jinja
#
# Usage:
#
# To update to the latest version:
# $ poe skeleton upgrade
#
# To update to version 1.2.3:
# $ poe skeleton upgrade 1.2.3
#
# To make a mechanized repo patch, but keep the current skeleton version:
# $ poe skeleton patch
#
# It's intended to be impossible to make a mechanized repo patch and update the skeleton
# at the same time.

# shellcheck disable=SC2005
# Automatically copied from https://github.com/bswck/skeleton/tree/0.0.2rc-62-g52ffbf3/handle-task-event.sh
# Comms
BOLD="\033[1m"
RED="\033[0;31m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
GREY="\033[0;90m"
NC="\033[0m"

UI_INFO="${BLUE}🛈${NC}"
UI_NOTE="${GREY}→${NC}"
UI_TICK="${GREEN}✔${NC}"
UI_CROSS="${RED}✘${NC}"

info() {
    echo -e "$UI_INFO $*"
}

note() {
    echo -e "$UI_NOTE $GREY$*$NC"
}

success() {
    echo -e "$UI_TICK $*"
}

silent() {
    "$1" "${@:2}" > /dev/null 2>&1
}

error() {
    local CODE=$1
    echo -e "$UI_CROSS ${*:2}" >&2
    return "$CODE"
}

setup_gh() {
    note "Calling GitHub setup hooks..."
    echo
    provision_gh_envs
}

determine_project_path() {
    # Determine the project path set by the preceding copier task process
    export PROJECT_PATH
    PROJECT_PATH=$(redis-cli get "$PROJECT_PATH_KEY")
}

create_gh_env() {
    # Ensure that the GitHub environment exists
    silent echo "$(jq -n '{"deployment_branch_policy": {"protected_branches": false,"custom_branch_policies": true}}' | gh api -H "Accept: application/vnd.github+json" -X PUT "/repos/bswck/lazy-imports/environments/$1" --input -)" || error 0 "Failed to ensure GitHub environment $BLUE$1$NC exists."
}

provision_gh_envs() {
    local SMOKESHOW_KEY
    local CODECOV_TOKEN
    local ENV_NAME="Upload Coverage"
    note "Creating a GitHub Actions environment $BLUE$ENV_NAME$GREY if necessary..."
    create_gh_env "$ENV_NAME"
    success "Environment $BLUE$ENV_NAME$NC exists."
    echo
    note "Checking if Smokeshow secret key needs to be created..."
    set +eE
    if test "$(gh secret list -e "$ENV_NAME" | grep -o SMOKESHOW_AUTH_KEY)"
    then
        note "Smokeshow secret key already set."
    else
        note "Smokeshow secret key does not exist yet."
        note "Creating Smokeshow secret key..."
        SMOKESHOW_KEY=$(smokeshow generate-key | grep SMOKESHOW_AUTH_KEY | grep -oP "='\K[^']+")
        gh secret set SMOKESHOW_AUTH_KEY --env "$ENV_NAME" --body "$SMOKESHOW_KEY" 2> /dev/null || error 0 "Failed to set Smokeshow secret key."
        echo
    fi
    note "Checking if Codecov secret token needs to be created..."
    if test "$(gh secret list -e "$ENV_NAME" | grep -o CODECOV_TOKEN)"
    then
        note "Codecov secret key already set."
    else
        note "Setting Codecov secret token..."
        CODECOV_TOKEN=$(keyring get codecov token)
        gh secret set CODECOV_TOKEN --env "$ENV_NAME" --body "$CODECOV_TOKEN" 2> /dev/null || error 0 "Failed to set Codecov secret token."
    fi
    set -eE
}
# End of copied code


set -eEuo pipefail

determine_new_ref() {
    # Determine the new skeleton revision set by the child process
    export NEW_REF
    NEW_REF=$(redis-cli get "$NEW_REF_KEY")
}

before_update_algorithm() {
    # Stash changes if any
    if test "$(git status --porcelain)"
    then
        error 0 "There are uncommitted changes in the project."
        error 1 "Stash them and continue."
    else
        note "Working tree clean, no need to stash."
    fi
}

do_update() {
    copier update --trust --vcs-ref "$1" "${@:2}"
}

run_update_algorithm() {
    # Run the underlying update algorithm
    export SKELETON_COMMAND
    SKELETON_COMMAND="${1:-"upgrade"}"
    if test "$SKELETON_COMMAND" = "upgrade-patch"
    then
        do_update "${2:-"HEAD"}"
    elif test "$SKELETON_COMMAND" = "upgrade"
    then
        do_update "${2:-"HEAD"}" --defaults
    elif test "$SKELETON_COMMAND" = "patch"
    then
        # shellcheck disable=SC2068
        do_update "$LAST_REF" ${@:3}
    else
        error 1 "Unknown update algorithm: '$1'"
    fi
    determine_new_ref
    determine_project_path
}

after_update_algorithm() {
    # Run post-update hooks, auto-commit changes
    cd "$PROJECT_PATH"
    info "${GREY}Previous skeleton revision:$NC $LAST_REF"
    info "${GREY}Current skeleton revision:$NC ${NEW_REF:-"N/A"}"
    local REVISION_PARAGRAPH="Skeleton revision: https://github.com/bswck/skeleton/tree/${NEW_REF:-"HEAD"}"
    note "Locking Poetry dependencies..."
    poetry lock
    note "Committing changes..."
    silent git add .
    silent git rm -f ./handle-task-event
    if test "$LAST_REF" = "$NEW_REF"
    then
        info "The version of the skeleton has not changed."
        local COMMIT_MSG="Mechanized patch at bswck/skeleton@$NEW_REF"
    else
        if test "$NEW_REF"
        then
            local COMMIT_MSG="Upgrade to bswck/skeleton@$NEW_REF"
        else
            local COMMIT_MSG="Upgrade to bswck/skeleton of unknown revision"
        fi
    fi
    silent redis-cli del "$PROJECT_PATH_KEY"
    silent redis-cli del "$NEW_REF_KEY"
    silent git commit --no-verify -m "$COMMIT_MSG" -m "$REVISION_PARAGRAPH"
    setup_gh && echo
}

main() {
    export LAST_REF="0.0.2rc-62-g52ffbf3"
    export PROJECT_PATH_KEY="$$_skeleton_project_path"
    export NEW_REF_KEY="$$_skeleton_new_ref"
    export LAST_LICENSE_NAME="MIT"

    cd "${PROJECT_PATH:=$(git rev-parse --show-toplevel)}" || exit 1
    echo
    info "${GREY}Last skeleton revision:$NC $LAST_REF"
    echo
    note "UPGRADE ROUTINE [1/3]: Running pre-update hooks."
    before_update_algorithm
    success "UPGRADE ROUTINE [1/3] COMPLETE."
    echo
    note "UPGRADE ROUTINE [2/3]: Running the underlying update algorithm."
    run_update_algorithm "$@"
    success "UPGRADE ROUTINE [2/3] COMPLETE."
    echo
    info "${GREY}Project path:$NC $PROJECT_PATH"
    echo
    note "UPGRADE ROUTINE [3/3]: Running post-update hooks."
    after_update_algorithm
    success "UPGRADE ROUTINE [3/3] COMPLETE."
    echo
    success "Done! 🎉"
    echo
    info "Your repository is now up to date with this bswck/skeleton revision:"
    echo -e "  ${BOLD}https://github.com/bswck/skeleton/tree/${NEW_REF:-"HEAD"}$NC"
}

main "$@"