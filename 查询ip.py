import dns.resolver
import dns.message
import dns.query
import re, time, os
from tqdm import tqdm

with open("域名列表.txt", "r") as f:
    域名列表 = f.read().splitlines()
域名列表 = [re.sub(r"\s", "", 域名) for 域名 in 域名列表 if 域名 and not 域名.startswith("#")]

with open("DNS列表.txt", "r") as f:
    DNS服务器列表 = f.read().splitlines()
DNS服务器列表 = [
    re.sub(r"\s", "", DNS服务器)
    for DNS服务器 in DNS服务器列表
    if DNS服务器 and not DNS服务器.startswith("#")
]

域名列表 = list(set(域名列表))
域名列表.sort()


def resolve_domain_any(domain, servers, responses, timeout):
    """使用指定的DNS服务器列表解析域名，尝试3次"""
    for server in servers:
        attempts = 0
        while attempts < 3:
            time.sleep(0.2)
            try:
                request = dns.message.make_query(domain, dns.rdatatype.ANY)
                response = dns.query.udp(request, server, timeout=timeout)
                for answer in response.answer:
                    for item in answer.items:
                        if item.rdtype == dns.rdatatype.A or item.rdtype == dns.rdatatype.AAAA:
                            responses.append(item)
                        elif item.rdtype == dns.rdatatype.CNAME:
                            resolve_domain_any(str(item.target), servers, responses, timeout)
                return
            except Exception as e:
                attempts += 1
                if attempts == 3:
                    print(f"{domain} 在 {server} 上解析失败。")
                else:
                    print(f"尝试 {attempts} 次使用 {server} 解析 {domain} 时发生错误: {e}")


# 解析域名并生成hosts文件内容
hosts_dict = {}
域名解析结果统计 = {
    "解析成功域名": [],
    "有多个IPv4和IPv6地址的域名": [],
    "解析失败域名": [],
}
for domain in tqdm(域名列表):
    responses = []
    resolve_domain_any(domain, DNS服务器列表, responses, timeout=5)
    if responses:
        # 区分ipv4和ipv6地址以便排除
        ipv4_addresses = []
        ipv6_addresses = []
        for response in responses:
            if response.rdtype == dns.rdatatype.A:
                ipv4_addresses.append(response.address)
            elif response.rdtype == dns.rdatatype.AAAA:
                ipv6_addresses.append(response.address)

        # 判断是否有多个IPv4和IPv6地址
        if len(ipv6_addresses) > 1 or len(ipv4_addresses) > 1:
            域名解析结果统计["有多个IPv4和IPv6地址的域名"].append(domain)
        else:
            域名解析结果统计["解析成功域名"].append(domain)
            for ipv6_address in set(ipv6_addresses):
                hosts_dict.setdefault(ipv6_address, []).append(domain)
            for ipv4_address in set(ipv4_addresses):
                hosts_dict.setdefault(ipv4_address, []).append(domain)

    else:
        域名解析结果统计["解析失败域名"].append(domain)



print(f"\n{'*'*30}\n共{len(域名列表)}个域名，成功解析{len(域名解析结果统计['解析成功域名'])}个")

if 域名解析结果统计["有多个IPv4和IPv6地址的域名"]:
    print("\n以下域名有多个IPv4和IPv6地址（考虑到负载均衡还是建议使用DNS而非hosts）：")
    for idx, domain in enumerate(域名解析结果统计["有多个IPv4和IPv6地址的域名"]):
        print(idx + 1, domain)

if 域名解析结果统计["解析失败域名"]:
    print("\n以下域名解析失败：")
    for idx, domain in enumerate(域名解析结果统计["解析失败域名"]):
        print(idx + 1, domain)

print(f"{'*'*30}")



host_content = ""
for ip, domains in hosts_dict.items():
    domains = list(set(domains))
    domains.sort()
    host_content += f"{ip}\t\t\t{'  '.join(domains)}\n"

# 读取原始hosts文件的内容
with open("hosts", "r") as f:
    original_content = f.read().splitlines()

# 准备两个列表，分别存储原始内容和新内容中的非注释行
original_lines = [line for line in original_content if line and not line.startswith("#")]
new_lines = [line for line in host_content.splitlines() if line and not line.startswith("#")]

# 比较非注释行，如果完全一样，则不更新文件
if original_lines == new_lines:
    print("hosts文件无需更新。")
else:
    # 如果有差异，更新hosts文件
    with open("hosts", "w") as f:
        f.write(host_content)
    print("hosts文件已更新。")
    # 使用git推送到仓库
    os.system("git add hosts")
    os.system("git commit -m 'update hosts'")
    os.system("git push origin master")
