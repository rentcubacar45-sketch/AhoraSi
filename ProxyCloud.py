class ProxyCloud(object):
    def __init__(self, ip, port, type='socks5', user=None, password=None):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.default = None
        self.type = type
    def set_default (self,socket):
        self.default = socket
    def as_dict_proxy(self):
        if self.user and self.password:
            auth = f'{self.user}:{self.password}@'
        else:
            auth = ''
        proxy_url = f'{self.type}://{auth}{self.ip}:{str(self.port)}'
        return {'http': proxy_url, 'https': proxy_url}

def parse(text):
    try:
        if '://' not in text:
            return None
        tokens = str(text).split('://', 1)
        type = tokens[0]
        rest = tokens[1]
        # Check for auth
        if '@' in rest:
            auth, ip_port = rest.rsplit('@', 1)
            user, password = auth.split(':', 1)
        else:
            user = None
            password = None
            ip_port = rest
        ip, port = ip_port.split(':', 1)
        port = int(port)
        return ProxyCloud(ip, port, type, user, password)
    except:
        pass
    return None


#enc = S5Crypto.encrypt('152.206.85.87:9050')
#proxy= f'socks5://' + enc
#print(proxy)