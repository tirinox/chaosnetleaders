export function numberWithCommas(x) {
  let parts = x.toString().split(".")
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",")
  return parts.join(".")
}

export function nicePercentFormat(x, total) {
  if (total === 0) {
    return 0
  } else {
    return (x / total * 100.0).toPrecision(2)
  }
}

export function volumeFormat (x) {
  const truncX = Math.round(x)
  return numberWithCommas(truncX)
}
