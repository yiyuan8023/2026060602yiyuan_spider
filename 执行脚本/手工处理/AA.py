import hashlib  # 导入哈希工具库
# 计算字符串“hello 哈希”的SHA-256哈希值（最常用的哈希算法）
hash_value = hashlib.sha256("hello 哈希".encode("utf-8")).hexdigest()
print("哈希值：", hash_value)