var proxy = "SOCKS 114.238.91.234:38801; DIRECT";

function FindProxyForURL(url, host) {
  if (shExpMatch(url, "*.ip138.com/*")) {
    return proxy;
  }
  if (shExpMatch(url, "*.163.com/*")) {
    return proxy;
  }
  return "DIRECT";
}