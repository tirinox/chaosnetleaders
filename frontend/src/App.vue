<template lang="html">
    <div>
        <b-navbar toggleable="md" type="dark" variant="dark" class="mb-5">
            <b-navbar-brand to="/">
                <img src="/img/icons/favicon-32x32.png" class="d-inline-block align-middle nav-logo pr-2" alt="Logo">
                {{ siteTitle }}
            </b-navbar-brand>

            <b-navbar-toggle target="nav-collapse"></b-navbar-toggle>

            <b-collapse id="nav-collapse" is-nav>
                <b-navbar-nav>

                    <b-nav-item-dropdown :text="statusTitle" right>
                        <b-dropdown-item>
                            TX Sync: {{ syncProgress | nicePercentFormat }} %
                            <small>({{ localTx }} of {{ remoteTx }})</small>
                        </b-dropdown-item>
                        <b-dropdown-item>
                            Value fill: {{ fillProgress | nicePercentFormat }} %
                            <small>({{ filledTx }} of {{ localTx }})</small>
                        </b-dropdown-item>
                    </b-nav-item-dropdown>

                    <b-nav-item to="/help" :active="$route.path === '/help'">Help</b-nav-item>

                    <b-nav-form class="ml-4">
                        <b-form-radio-group
                            button-variant="success"
                            v-model="selected"
                            :options="currencyOptions"
                            name="buttons-1"
                            buttons
                            @change="onCurrencySwitch"
                        ></b-form-radio-group>
                    </b-nav-form>

                </b-navbar-nav>

                <b-navbar-nav class="ml-auto">
                    <b-nav-item right href="https://leaderboard.thornode.org/" :active="$route.path === '/'" v-if="isBepSwap">Go to MCCN version</b-nav-item>
                    <b-nav-item right href="https://leaderboard-bepswap.thornode.org/" :active="$route.path === '/'" v-else>Go to Bepswap version</b-nav-item>
                </b-navbar-nav>
            </b-collapse>

        </b-navbar>

        <div class="container">
            <router-view/>
        </div>

        <footer class="footer">
            <div class="container">
                <span class="text-muted">This is an beta version {{ packageJson }}! Made by community ⚡</span>
            </div>
        </footer>
    </div>
</template>

<script>

import {ON_CURRENCY_CHANGE, EventBus} from '@/lib/bus'
import {getNetworkId, NETWORK_CHAOSNET_BEP2, NETWORK_CHAOSNET_MUTLI, NETWORK_TESTNET_MULTI} from "@/lib/misc";
import axios from "axios";
import {nicePercentFormat} from "@/lib/digits";

export default {
    name: 'App',
    data() {
        return {
            selected: 'rune',
            loading: false,
            syncProgress: 0.0,
            fillProgress: 0.0,
            localTx: 0,
            filledTx: 0,
            remoteTx: 0
        }
    },
    filters: {
        nicePercentFormat
    },
    methods: {
        onCurrencySwitch(v) {
            EventBus.$emit(ON_CURRENCY_CHANGE, v)
        },

        onStatusCheck() {
            const url = `/api/v1/progress`

            this.loading = true
            axios
                .get(url)
                .then(this.updateStatus)
                .finally(() => (this.loading = false))
        },

        updateStatus(j) {
            let syncInfo = j.data.tx_sync
            this.syncProgress = syncInfo.progress
            this.localTx = syncInfo.local_tx_count
            this.remoteTx = syncInfo.remote_tx_count

            let fillInfo = j.data.value_fill
            this.filledTx = fillInfo.filled_tx
            this.fillProgress = fillInfo.progress
        }
    },
    computed: {
        currencyOptions() {
            return [
                {
                    text: 'RUNE',
                    value: 'rune',
                },
                {
                    text: 'USD',
                    value: 'usd',
                }
            ]
        },

        siteTitle() {
            let network = getNetworkId()
            if (network === NETWORK_CHAOSNET_BEP2) {
                return 'Chaosnetleaders'
            } else if (network === NETWORK_CHAOSNET_MUTLI) {
                return 'MCCN Leaderboard'
            } else if (network === NETWORK_TESTNET_MULTI) {
                return 'MCTN Leaderboard'
            } else {
                return 'Unknown network!'
            }
        },

        isBepSwap() {
            return getNetworkId() === NETWORK_CHAOSNET_BEP2
        },

        statusTitle() {
            let emoji = '💔'
            let f = this.fillProgress
            let s = this.syncProgress
            if(f >= 99 && s >= 90) {
                emoji = '⚡'
            }
            return emoji + ' Status'
        },

        packageJson() {
            return process.env.VUE_APP_VERSION || '0'
        }
    },
    mounted() {
        this.onStatusCheck()
        setInterval(this.onStatusCheck, 10 * 1000)
    }
}
</script>

<style>
.footer {
    padding: 5px;
}

</style>
