<template>
    <div class="row">
        <div class="col-12">
            <h1>{{ pageTitle }}</h1>

            <p class="subtitle">
                <b-spinner label="Loading" small v-if="loading"></b-spinner>
                <span class="text-muted">Since</span>
                <em v-if="data.since > 0">
                    {{ data.since | prettyDateFromTimestamp }}
                </em>
                &nbsp;
                <span class="text-muted" v-if="data.since <= 0">the beginning of time...</span>
                <span v-if="data.to < 2147483647">
                    <span class="text-muted"> to</span>
                    <em>{{ data.to | prettyDateFromTimestamp }}</em>
                </span>
            </p>

            <div>
                <b-button variant="link" v-on:click="navigateToDate('all')">All time</b-button>
                |
                <b-button variant="link" v-on:click="navigateToDate(30)">Last month</b-button>
                |
                <b-button variant="link" v-on:click="navigateToDate(7)">Last week</b-button>
                |
                <b-button variant="link" v-on:click="navigateToDate(1)">Last day</b-button>
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
                <LeaderRow v-for="(item, index) in data.leaderboard" :key="item.user_address"
                           :index="index"
                           :network="network"
                           :item="item"
                           :place="getLeaderPlace(index)"
                           :currency="currency"
                           :total-volume="data.chaosnet_volume"
                           :hide-value="loading">
                </LeaderRow>
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
import {addCurrency, nicePercentFormat, prettyDateFromTimestamp, volumeFormat} from '@/lib/digits'
import {shortAddress} from '@/lib/address'
import {EventBus, ON_CURRENCY_CHANGE} from '@/lib/bus'
import {getNetworkId, NETWORK_CHAOSNET_BEP2, NETWORK_CHAOSNET_MUTLI, NETWORK_TESTNET_MULTI} from "@/lib/misc";
import LeaderRow from "@/components/LeaderRow";

const LIMIT_PER_PAGE = 100

function daysAgo(d) {
    const day = 60 * 60 * 24
    const currentTs = Math.floor(Date.now() / 1000)
    return currentTs - day * d
}

export default {
    name: 'LeaderboardComponent',
    components: {LeaderRow},
    data() {
        return {
            data: [],
            loading: false,
            currentPage: 1,
            itemsPerPage: LIMIT_PER_PAGE,
            network: '',
        }
    },

    computed: {
        pageTitle() {
            let network = this.network
            if (network === NETWORK_CHAOSNET_BEP2) {
                return 'Chaosnet Leaderboard'
            } else if (network === NETWORK_CHAOSNET_MUTLI) {
                return 'Multi-Chain Chaosnet Leaderboard'
            } else if (network === NETWORK_TESTNET_MULTI) {
                return 'Multi-Chain Testnet Leaderboard'
            } else {
                return 'Unknown network!'
            }
        },

        realPage() {
            return parseInt(this.$route.query.page, 10) || 0
        },
        currency() {
            return this.$route.query.currency || 'rune'
        },
        ts_since() {
            return parseInt(this.$route.query.ts_since, 10) || daysAgo(7)  // 1 week by default
        },
        ts_to() {
            return parseInt(this.$route.query.ts_to, 10) || -1
        },

    },

    methods: {
        navigateToDate(d) {
            let ts_since
            let ts_to
            if (d === 'all') {
                ts_since = -1
                ts_to = -1
            } else {
                ts_since = daysAgo(d)
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
            }).catch(() => {
            })
        },

        getLeaderPlace(index) {
            return index + 1 + this.realPage * this.itemsPerPage
        },

        navigateToPage(page) {
            page = +page
            this.updatePath({page})
        },

        fetchLeaders() {
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
        },

    },

    filters: {
        volumeFormat,
        prettyDateFromTimestamp,
        nicePercentFormat,
        shortAddress,
        addCurrency
    },

    watch: {
        '$route.query.ts_since'() {
            this.fetchLeaders()
        },
        '$route.query.page'() {
            this.fetchLeaders()
        },
        '$route.query.currency'() {
            this.fetchLeaders()
        },
        currentPage(page) {
            this.navigateToPage(page - 1)
        }
    },

    mounted() {
        this.network = getNetworkId()
        this.fetchLeaders()
        EventBus.$on(ON_CURRENCY_CHANGE, (currency) => {
            this.updatePath({currency})
        })
    }
}

</script>
