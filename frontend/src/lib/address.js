export function shortAddress (addr, strLen) {
  strLen = strLen || 16
  if (addr.length <= strLen) return addr

  const separator = '...'

  const sepLen = separator.length,
    charsToShow = strLen - sepLen,
    frontChars = Math.ceil(charsToShow / 2),
    backChars = Math.floor(charsToShow / 2)

  return addr.substr(0, frontChars) +
    separator +
    addr.substr(addr.length - backChars)
}
