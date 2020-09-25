<template>

    <div class="row">
      <div class="col-12">
      <h1>Chaosnet Leaderboard</h1>
        <p class="subtitle">Since <em>{{ data.since | prettyDateFromTimestamp }}</em> </p>
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
          <td>{{ index + 1 }}.</td>
          <td>
            <a :href="'https://thorchain.net/addresses/' + item.input_address" target="_blank">
              {{ item.input_address | shortAddress }}
            </a>
          </td>
          <td><strong>{{ item.total_volume | volume }} ᚱ</strong></td>
          <td><small>{{ item.date | prettyDateFromTimestamp }}</small></td>
        </tr>
      </table>

      </div>
    </div>

</template>

<script>

import axios from 'axios'

export default {
  name: 'LeaderboardComponent',
  data () {
    return {
      data: []
    }
  },

  filters: {
    volume(x) {
      return Math.round(x)
    },
    prettyDateFromTimestamp(unix_timestamp) {
      let date = new Date(unix_timestamp * 1000)
      return date.toUTCString()
    },
    shortAddress(addr, strLen) {
      strLen = strLen || 16
      if (addr.length <= strLen) return addr;

      const separator = '...';

      var sepLen = separator.length,
        charsToShow = strLen - sepLen,
        frontChars = Math.ceil(charsToShow/2),
        backChars = Math.floor(charsToShow/2);

      return addr.substr(0, frontChars) +
        separator +
        addr.substr(addr.length - backChars);
    }
  },

  mounted () {
    axios
      .get('/api/v1/leaderboard')
      .then(response => (this.data = response.data))
  }
}

</script>
