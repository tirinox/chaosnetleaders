<template>
  <div class="container">
    <h1>Chaosnet Leaderboard</h1>
    <p class="subtitle">Since {{ data.since | prettyDateFromTimestamp }} </p>
    <table>
      <thead>
        <td>Place</td>
        <td>Address</td>
        <td>Volume</td>
        <td>Last activity</td>
      </thead>
      <tr v-for="(item, index) in data.leaderboard" :key="item.input_address">
        <td>{{ index + 1 }}.</td>
        <td>
          <a :href="'https://explorer.binance.org/address/' + item.input_address">{{ item.input_address }}</a>
        </td>
        <td><strong>{{ item.total_volume | volume }} ᚱ</strong></td>
        <td><small>{{ item.date | prettyDateFromTimestamp }}</small></td>
      </tr>
    </table>

    <br><br>
    <small>This is an alpha version 0.0.1!</small>
  </div>
</template>

<script>

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
    }
  },
  mounted () {
    axios
      .get('/api/v1/leaderboard')
      .then(response => (this.data = response.data))
  }
}

</script>

<style lang="scss" scoped>
h1 {
  padding-left: 30px;
}
table {
  padding: 10px;
  padding-left: 30px;
}

thead {
  font-weight: bold;
}

.subtitle {
  padding-left: 30px;
}

td {
  padding: 5px;
  font-size: 14pt;
}

</style>
