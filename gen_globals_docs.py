from ichor.hpc.globals import Globals

with open("globals.md", "w") as f:
    globals = Globals()
    f.write("| Name | Type | Default Value |\n")
    f.write("| --- | --- | --- |\n")
    for global_variable in globals._global_variables:
        try:
            if global_variable not in globals._protected:
                f.write(
                    f"| {global_variable} | {globals.__annotations__[global_variable].__name__} | {globals._defaults[global_variable]} |\n"
                )
        except:
            pass
