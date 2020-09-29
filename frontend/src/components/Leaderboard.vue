<template>
  <div class="row">
    <div class="col-12">
      <h1>Chaosnet Leaderboard</h1>

      <p class="subtitle">
        <b-spinner label="Loading" small v-if="loading"></b-spinner>
        Since <em>{{ data.since | prettyDateFromTimestamp }}</em></p>
      <div>
        <b-button-group size="sm" class="mb-2">
          <b-button variant="warning" v-on:click="navigateToDate('competition')">Competition</b-button>
          <b-button variant="primary" v-on:click="navigateToDate('all')">All time</b-button>
          <b-button variant="success" v-on:click="navigateToDate(30)">Last month</b-button>
          <b-button variant="primary" v-on:click="navigateToDate(7)">Last week</b-button>
          <b-button variant="success" v-on:click="navigateToDate(1)">Last day</b-button>
        </b-button-group>
      </div>

      <table class="table table-striped">
        <thead>
          <tr>
            <th scope="col">Place</th>
            <th scope="col">Address</th>
            <th scope="col">Volume</th>
            <th scope="col">Last activity</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="(item, index) in data.leaderboard" :key="item.input_address">
            <th scope="row">
              <span class="lead">{{ getPaginatedIndex(index) }}.</span>
            </th>

            <td>
              <a :href="'https://thorchain.net/addresses/' + item.input_address" target="_blank">
                {{ item.input_address | shortAddress }}
              </a>
            </td>

            <td>
              <h5>{{ item.total_volume | volumeFormat }} ᚱ</h5>
              <small class="text-muted">
                {{ item.total_volume | nicePercentFormat(data.chaosnet_volume) }} % with
                {{ item.n }} txs
              </small>

            </td>

            <td>
              <small>{{ item.date | prettyDateFromTimestamp }}</small>
            </td>
          </tr>
        </tbody>
      </table>

      <b-pagination v-if="data.leaderboard"
        v-model="currentPage"
        :total-rows="data.participants"
        :per-page="itemsPerPage"
        first-text="First"
        prev-text="Prev"
        next-text="Next"
        last-text="Last"
      ></b-pagination>

      <p>Total volume: <strong>{{ data.chaosnet_volume | volumeFormat }} ᚱ</strong></p>

    </div>
  </div>

</template>

<script>

import axios from 'axios'
import { nicePercentFormat, volumeFormat } from '@/lib/digits'
import { shortAddress } from '@/lib/address'

const COMPETITION_TIMESTAMP = 1599739200  // 12pm UTC, Thursday 10th September 2020
const LIMIT_PER_PAGE = 100

export default {
  name: 'LeaderboardComponent',
  data () {
    return {
      data: [],
      loading: false,
      currentPage: 1,
      itemsPerPage: LIMIT_PER_PAGE
    }
  },

  computed: {
      realPage() {
        return parseInt(this.$route.query.page, 10) || 0
      }
  },

  methods: {
    navigateToDate(d) {
      let ts
      if(d === 'all') {
        ts = -1
      } else if(d === 'competition') {
        ts = COMPETITION_TIMESTAMP
      } else {
        const day = 60 * 60 * 24
        const currentTs = Math.floor(Date.now() / 1000)
        ts = currentTs - d * day
      }
      this.$router.replace({path: '/', query: {
        ...this.$route.query,
          ts,
          page: 0 } } )
    },

    getPaginatedIndex(index) {
      return index + 1 + this.realPage * this.itemsPerPage
    },

    navigateToPage(page) {
      page = +page
      this.$router.replace({path: '/', query: { ...this.$route.query, page } } )
    },

    fetchLeaders() {
      let since = parseInt(this.$route.query.ts, 10) || COMPETITION_TIMESTAMP
      if(since < 0) {
        since = 0  // all time
      }

      const offset = this.realPage * this.itemsPerPage
      const url = `/api/v1/leaderboard?offset=${offset}&since=${since}`;

      this.loading = true
      axios
        .get(url)
        .then(response => (this.data = response.data))
        .finally(() => (this.loading = false))
    }
  },

  filters: {
    volumeFormat,
    prettyDateFromTimestamp (unix_timestamp) {
      let date = new Date(unix_timestamp * 1000)
      return date.toUTCString()
    },
    nicePercentFormat,
    shortAddress
  },

  watch: {
    '$route.query.ts'() {
      this.fetchLeaders();
    },
    '$route.query.page'() {
      this.fetchLeaders();
    },
    currentPage(page) {
      this.navigateToPage(page - 1)
    }
  },

  mounted () {
    this.fetchLeaders()
  }
}

</script>
