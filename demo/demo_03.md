### USER
怎么用 python 连接 ldap 判断 ldap 背后的用的是什么 ad 方案

### ASSISTANT
在 Python 中连接 LDAP 并判断其背后使用的 Active Directory（AD）方案，可以通过分析 LDAP 服务器返回的属性、命名空间（DIT 结构）、对象类（objectClass）以及特定的 AD 属性来推断。虽然 LDAP 是一种协议，可以被多种目录服务（如 OpenLDAP、389 Directory Server、Microsoft Active Directory 等）实现，但 Microsoft AD 有一些独特的特征可以用来识别。

下面是一个完整的流程和代码示例，教你如何用 Python 连接 LDAP 并判断是否为 Active Directory 及其类型（如标准 AD、Azure AD 等）。

---

### ✅ 步骤说明：

1. 使用 `python-ldap` 或 `ldap3` 库连接 LDAP 服务器。
2. 绑定（登录）到 LDAP 服务器（匿名或认证方式）。
3. 查询根 DSE（DIT 的根条目）获取 `namingContexts`、`supportedLDAPVersion`、`vendorName`、`objectClass` 等信息。
4. 分析返回的属性，判断是否为 Active Directory。
5. 进一步判断是本地 AD 还是 Azure AD。

---

### 🛠️ 推荐库：`ldap3`（更现代、易用）

```bash
pip install ldap3
```

---

### ✅ 示例代码：判断 LDAP 是否为 Active Directory

```python
from ldap3 import Server, Connection, ALL, SUBTREE

def detect_ad_ldap(ldap_host, port=389, use_ssl=False, user=None, password=None, timeout=10):
    """
    连接 LDAP 服务器并判断是否为 Active Directory
    返回: 字典，包含是否为 AD、AD 类型等信息
    """
    server = Server(ldap_host, port=port, use_ssl=use_ssl, get_info=ALL)

    # 尝试建立连接（不立即绑定）
    try:
        conn = Connection(server, user=user, password=password, auto_bind=True, receive_timeout=timeout)
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

    info = {
        'success': True,
        'is_ad': False,
        'ad_type': None,  # 'on-premise', 'azure_ad', 'unknown'
        'vendor_name': server.info.vendor_name if server.info else None,
        'naming_contexts': server.info.naming_contexts if server.info else [],
        'root_dn': server.info.raw['defaultNamingContext'][0] if server.info and 'defaultNamingContext' in server.info.raw else None,
        'supported_features': server.info.supported_features if server.info else [],
        'ldap_version': server.info.supported_ldap_version if server.info else None,
    }

    # 判断是否为 Active Directory 的关键点
    if server.info:
        # 1. 检查 vendorName
        if server.info.vendor_name and 'Microsoft' in server.info.vendor_name:
            info['is_ad'] = True
            info['ad_type'] = 'on-premise'

        # 2. 检查 namingContexts 是否包含典型的 AD 域格式
        for nc in info['naming_contexts']:
            if b'domainDns' in nc or str(nc).lower().startswith('dc='):
                info['is_ad'] = True
                if not info['ad_type']:
                    info['ad_type'] = 'on-premise'

        # 3. 查询 rootDSE 的 objectClass
        conn.search('', '(objectClass=*)', search_scope=SUBTREE, attributes=['objectClass'])
        if conn.entries:
            for entry in conn.entries:
                oc = entry.entry_attributes
                if 'objectClass' in oc:
                    oc_vals = [str(o).lower() for o in entry.objectClass.values]
                    if 'top' in oc_vals and 'domain' in oc_vals and 'configuration' in oc_vals:
                        info['is_ad'] = True
                        if not info['ad_type']:
                            info['ad_type'] = 'on-premise'

        # 4. 检查是否有 AD 特有的属性或 OID
        ad_oids = [
            '1.2.840.113556.1.4.319',  # LDAP_SERVER_PAGING_OID (AD 支持分页)
            '1.2.840.113556.1.4.801',  # 其他 AD 扩展
        ]
        if server.info.supported_extensions:
            supported_oids = [str(oid) for oid in server.info.supported_extensions]
            if any(oid in supported_oids for oid in ad_oids):
                info['is_ad'] = True
                if not info['ad_type']:
                    info['ad_type'] = 'on-premise'

        # 5. Azure AD 的判断（较难直接判断，但可通过行为推断）
        # Azure AD 通常不开放原生 LDAP 端口（389/636），但某些混合部署可能开启
        # 若 server.info.vendor_name 包含 "Azure" 或域名包含 .onmicrosoft.com
        if info['root_dn']:
            if '.onmicrosoft.com' in info['root_dn'].lower():
                info['ad_type'] = 'azure_ad_hybrid'
            elif 'Azure' in str(server.info.vendor_name):
                info['ad_type'] = 'azure_ad'

    conn.unbind()
    return info

# === 使用示例 ===
if __name__ == '__main__':
    result = detect_ad_ldap(
        ldap_host='your-ad-server.com',
        port=389,
        user='CN=admin,DC=example,DC=com',
        password='yourpassword'
    )
    print(result)
```

---

### 🔍 判断依据总结：

| 特征 | 是否为 AD |
|------|----------|
| `vendorName` 包含 "Microsoft" | ✅ 很可能是 AD |
| `namingContexts` 包含 `DC=`, `CN=Configuration` | ✅ 典型 AD 结构 |
| 支持分页控制（OID `1.2.840.113556.1.4.319`） | ✅ AD 特性 |
| 存在 `domainDNS` 对象类 | ✅ AD 特有 |
| `defaultNamingContext` 是 `.onmicrosoft.com` | ⚠️ 可能是 Azure AD 混合部署 |

> ⚠️ 注意：Azure AD **原生不支持 LDAP 协议**，但 Azure AD Domain Services（AADDS）提供 LDAP 接口。所以如果你能通过 LDAP 连上，很可能是 AADDS 或本地 AD。

---

### ❓ 常见问题

**Q: 能否判断是 Windows Server 哪个版本的 AD？**
A: 可以通过 `rootDSE` 的 `serverName`、`ldapServiceName` 或 `supportedCapabilities` 中的 OID 推断，例如：
- `1.2.840.113556.1.4.800` 表示 Windows 2000
- `1.2.840.113556.1.4.1670` 表示 Windows 2008 R2+

**Q: 匿名绑定是否可行？**
A: 有些 AD 允许匿名读取 rootDSE，但大多数企业会禁用。建议使用有权限的账号。

---

### ✅ 总结

通过 `ldap3` 库连接 LDAP，读取 `rootDSE` 信息，结合以下特征可判断是否为 AD：

- vendorName 是否为 Microsoft
- 命名上下文是否为 `DC=xxx`
- 是否支持 AD 特有的 OID
