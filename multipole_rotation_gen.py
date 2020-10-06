d = {"x": 0, "y": 1, "z": 2}
axes = ["x", "y", "z"]

def indices_to_index(*indices):
    o = ""
    for i in indices:
        o += axes[i]
    return o

def indices_to_index_dict(d, *indices):
    o = ""
    for i in indices:
        o += axes[i]
    return d[o]

with open("multipole.txt", "w") as f:
    r = []
    order = ["x", "y", "z"]
    for i in range(3):
        i_ = list(sorted([i]))
        if not i_ in r:
            print(i_, r)
            r.append(i_)
            idx = indices_to_index(i)
            d = f"D_{idx} = "
            for a in range(3):
                idx = indices_to_index(*sorted([a]))
                d += f" C[{i}][{a}]*d_{idx} +"
            f.write(d.rstrip("+") + "\n")
    f.write("\n")
    r = []
    order = ["xx", "xy", "xz", "yy", "yz", "zz"]
    for i in range(3):
        for j in range(3):
            i_j = list(sorted([i, j]))
            if not i_j in r:
                print(i_j, r)
                r.append(i_j)
                idx = indices_to_index(i, j)
                q = f"Q_{idx} = "
                for a in range(3):
                    for b in range(3):
                        idx = indices_to_index(*sorted([a, b]))
                        q += f" C[{i}][{a}]*C[{j}][{b}]*q_{idx} +"
                f.write(q.rstrip("+") + "\n")
    f.write("\n")
    r = []
    order = ["xxx", "xxy", "xxz", "xyy", "xyz", "xzz", "yyy", "yyz", "yzz", "zzz"]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                i_j_k = list(sorted([i, j, k]))
                if not i_j_k in r:
                    print(i_j_k, r)
                    r.append(i_j_k)
                    idx = indices_to_index(i, j, k)
                    o = f"O_{idx} = "
                    for a in range(3):
                        for b in range(3):
                            for c in range(3):
                                idx = indices_to_index(*sorted([a, b, c]))
                                o += f" C[{i}][{a}]*C[{j}][{b}]*C[{k}][{c}]*o_{idx} +"
                    f.write(o.rstrip("+") + "\n")
    f.write("\n")
    r = []
    order = ["xxxx", "xxxy", "xxxz", "xxyy", "xxyz", "xxzz", "xyyy", "xyyz", "xyzz", "xzzz", "yyyy", "yyyz", "yyzz", "yzzz", "zzzz"]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for l in range(3):
                    i_j_k_l = list(sorted([i, j, k, l]))
                    if not i_j_k_l in r:
                        print(i_j_k_l, r)
                        r.append(i_j_k_l)
                        idx = indices_to_index(i, j, k, l)
                        h = f"H_{idx} = "
                        for a in range(3):
                            for b in range(3):
                                for c in range(3):
                                    for d in range(3):
                                        idx = indices_to_index(*sorted([a, b, c, d]))
                                        h += f" C[{i}][{a}]*C[{j}][{b}]*C[{k}][{c}]*C[{l}][{d}]*h_{idx} +"
                        f.write(h.rstrip("+") + "\n")


