'''
此代码用于整理域名列表，去除重复项，并按照字母顺序排列，将#开头的注释排在最后。
'''

import re

with open("域名列表.txt", "r") as f:
    域名列表 = f.read().splitlines()
域名列表 = [re.sub(r"\s", "", 域名) for 域名 in 域名列表 if 域名]

域名列表 = list(set(域名列表))
域名列表.sort(key=lambda x: x if x[0]!='#' else chr(0x10ffff))

with open("域名列表.txt", "w") as f:
    f.write("\n".join(域名列表))
