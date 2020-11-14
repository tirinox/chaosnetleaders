<template>
  <div class="row">
    <div class="col-12">
      <h1>Chaosnet Leaderboard</h1>

      <p class="subtitle">
        <b-spinner label="Loading" small v-if="loading"></b-spinner>
        <span class="text-muted">Since</span>
        <em v-if="data.since > 0">
          {{ data.since | prettyDateFromTimestamp }}
        </em>
        <span class="text-muted" v-if="data.since <= 0">
            the beginning of time...
          </span>
        <span v-if="data.to < 2147483647">
          <span class="text-muted"> to</span> <em>{{ data.to | prettyDateFromTimestamp }}</em>
        </span>
      </p>

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
            <a :href="'https://viewblock.io/thorchain/address/' + item.input_address" target="_blank">
              {{ item.input_address | shortAddress }}
            </a>
          </td>

          <td>
            <h5>{{ item.total_volume | volumeFormat | addCurrency(currency) }}</h5>
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

      <p>Total volume: <strong>{{ data.chaosnet_volume | volumeFormat | addCurrency(currency) }}</strong></p>

    </div>
  </div>

</template>

<script>

import axios from 'axios'
import { nicePercentFormat, volumeFormat } from '@/lib/digits'
import { shortAddress } from '@/lib/address'
import { EventBus, ON_CURRENCY_CHANGE } from '@/lib/bus'

const COMPETITION_START_TIMESTAMP = 1599739200  // 12pm UTC, Thursday 10th September 2020
const COMPETITION_ENDING_TIMESTAMP = 1602158400  // 12pm UTC, Thursday 8th October 2020
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
    realPage () {
      return parseInt(this.$route.query.page, 10) || 0
    },
    currency () {
      return this.$route.query.currency || 'rune'
    },
    ts_since () {
      return parseInt(this.$route.query.ts_since, 10) || COMPETITION_START_TIMESTAMP
    },
    ts_to () {
      return parseInt(this.$route.query.ts_to, 10) || COMPETITION_ENDING_TIMESTAMP
    },
  },

  methods: {
    navigateToDate (d) {
      let ts_since
      let ts_to
      if (d === 'all') {
        ts_since = -1
        ts_to = -1
      } else if (d === 'competition') {
        ts_since = COMPETITION_START_TIMESTAMP
        ts_to = COMPETITION_ENDING_TIMESTAMP
      } else {
        const day = 60 * 60 * 24
        const currentTs = Math.floor(Date.now() / 1000)
        ts_since = currentTs - d * day
        ts_to = -1
      }

      this.updatePath({
        ts_since,
        ts_to,
        page: 0
      })
    },

    updatePath(params) {
      this.$router.replace({
        path: '/', query: {
          ...this.$route.query,
          ...params,
        }
      }).catch(() => {})
    },

    getPaginatedIndex (index) {
      return index + 1 + this.realPage * this.itemsPerPage
    },

    navigateToPage (page) {
      page = +page
      this.updatePath({ page })
    },

    fetchLeaders () {
      let ts_since = this.ts_since
      let ts_to = this.ts_to
      if (ts_since < 0) {
        ts_since = 0  // all time
      }
      if (ts_to < 0) {
        ts_to = 0  // to the end of the world
      }

      const offset = this.realPage * this.itemsPerPage
      const url = `/api/v1/leaderboard?offset=${offset}&since=${ts_since}&to=${ts_to}&currency=${this.currency}`

      this.loading = true
      axios
        .get(url)
        .then(this.parseLb)
        .finally(() => (this.loading = false))
    },

    parseLb(response) {
      this.data = response.data
    }
  },

  filters: {
    volumeFormat,
    prettyDateFromTimestamp (unix_timestamp) {
      let date = new Date(unix_timestamp * 1000)
      return date.toUTCString()
    },
    nicePercentFormat,
    shortAddress,
    addCurrency(data, curr) {
      if(curr === 'rune') {
        return data + ' ᚱ'
      } else {
        return '$ ' + data
      }
    }
  },

  watch: {
    '$route.query.ts_since' () {
      this.fetchLeaders()
    },
    '$route.query.page' () {
      this.fetchLeaders()
    },
    '$route.query.currency' () {
      this.fetchLeaders()
    },
    currentPage (page) {
      this.navigateToPage(page - 1)
    }
  },

  mounted () {
    this.fetchLeaders()
    EventBus.$on(ON_CURRENCY_CHANGE, (currency) => {
      this.updatePath({ currency })
    })
  }
}

</script>
