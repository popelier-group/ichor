

# def natural_sort(iterable, key=None, reverse=False):
#     prog = re.compile(r"(\d+)")
#
#     def alphanum_key(element):
#         return [
#             int(c) if c.isdigit() else c for c in prog.findall(element)
#         ]
#
#     return sorted(iterable, key=alphanum_key, reverse=reverse)