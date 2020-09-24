<template>
  <div class="container">
    <h1>Chaosnet Leaderboard</h1>

    <table>
      <tr v-for="(item, index) in items" :key="item.input_address">
        <td>{{ index + 1 }}.</td>
        <td>
          <a :href="'https://explorer.binance.org/address/' + item.input_address">{{ item.input_address }}</a>
        </td>
        <td>{{ Math.round(item.total_volume) }} ᚱ</td>
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
      items: []
    }
  },
  mounted () {
    axios
      .get('/api/v1/leaderboard')
      .then(response => (this.items = response.data))
  }
}

</script>

<style lang="scss" scoped>
h1 {
  padding-left: 30px;
}
table {
  padding: 10px;
}

td {
  padding: 5px;
  font-size: 14pt;
}

</style>
