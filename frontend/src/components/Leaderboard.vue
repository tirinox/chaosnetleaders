<template>
  <div class="row">
    <div class="col-12">
      <h1>Chaosnet Leaderboard</h1>
      <p class="subtitle">Since <em>{{ data.since | prettyDateFromTimestamp }}</em></p>
      <table class="table">
        <thead>
        <tr>
          <th>Place</th>
          <th>Address</th>
          <th>Volume</th>
          <th>Last activity</th>
        </tr>
        </thead>
        <tr v-for="(item, index) in data.leaderboard" :key="item.input_address">
          <td><span class="lead">{{ index + 1 }}.</span></td>
          <td>
            <a :href="'https://thorchain.net/addresses/' + item.input_address" target="_blank">
              {{ item.input_address | shortAddress }}
            </a>
          </td>
          <td>
            <strong>{{ item.total_volume | volumeFormat }} ᚱ</strong>
            <small class="text-muted"> ({{ item.total_volume | nicePercentFormat(data.chaosnet_volume) }} %)</small>
          </td>
          <td><small>{{ item.date | prettyDateFromTimestamp }}</small></td>
        </tr>
      </table>
      <p>Total volume: <strong>{{ data.chaosnet_volume | volumeFormat }} ᚱ</strong></p>

    </div>
  </div>

</template>

<script>

import axios from 'axios'
import { nicePercentFormat, volumeFormat } from '@/lib/digits'

export default {
  name: 'LeaderboardComponent',
  data () {
    return {
      data: []
    }
  },

  filters: {
    volumeFormat,
    prettyDateFromTimestamp (unix_timestamp) {
      let date = new Date(unix_timestamp * 1000)
      return date.toUTCString()
    },
    nicePercentFormat,
    shortAddress (addr, strLen) {
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
  },

  mounted () {
    axios
      .get('/api/v1/leaderboard')
      .then(response => (this.data = response.data))
  }
}

</script>
