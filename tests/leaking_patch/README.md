Carl Meyer:
> The leaking-patch problem is basically inherent to lazy imports; it's just one particular case of the general problem that if you delay an import, the global state may be different when the import occurs than it was when the import statement executed. You can whack-a-mole cases of this general problem by trying to preserve/restore particular aspects of the global state (e.g. `sys.path`, `sys.meta_path`.) You could presumably whack-a-mole the leaking-patch case by having lazy import be aware of all active patches (presuming all patches go through a particular API like `unittest.mock.patch` which tracks active patches) and temporarily revert them while resolving the import.
>
> (...)
>
> The harmful consequence is that if in module `a` you have a lazy import `from b import C`, and you have a test that temporarily patches `b.C` to be some kind of mock object, you can end up with module `a` unintentionally importing the mock of `C` instead of the real `C`, and that will be permanent (it won't be reverted when the temporary patch of `b.C` ends).

The reproduction of the problem lives in this directory.<br>
Shoutout to Carl for bringing this up!