export function numberWithCommas(x) {
    let parts = x.toString().split(".")
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",")
    return parts.join(".")
}

export function nicePercentFormat(x, total) {
    if(typeof total === 'undefined') {
        return x.toFixed(2)
    } else if (total === 0) {
        return 0
    } else {
        return (x / total * 100.0).toFixed(3)
    }
}

export function volumeFormat(x) {
    const truncX = Math.round(x)
    return numberWithCommas(truncX)
}

export function addCurrency(data, curr) {
    if (curr === 'rune') {
        return data + ' ᚱ'
    } else {
        return '$ ' + data
    }
}

export function prettyDateFromTimestamp(unix_timestamp) {
    let date = new Date(unix_timestamp * 1000)
    return date.toUTCString()
}