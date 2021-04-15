<template>
    <tr>
        <th scope="row">
            <span class="lead">{{ place }}.</span>
        </th>

        <td>
            <a :href="viewAddressInExplorer(item.user_address)" target="_blank">
                {{ item.user_address | shortAddress }}
            </a>
        </td>

        <td>
            <transition name="fade">
                <div v-show="!hideValue">
                    <h5>{{ item.total_volume | volumeFormat | addCurrency(currency) }}</h5>
                    <small class="text-muted">
                        {{ item.total_volume | nicePercentFormat(totalVolume) }} % with
                        {{ item.n }} txs
                    </small>
                </div>
            </transition>
        </td>

        <td>
            <small>{{ item.date | prettyDateFromTimestamp }}</small>
        </td>
    </tr>
</template>

<script>

import {NETWORK_CHAOSNET_BEP2, NETWORK_CHAOSNET_MUTLI, NETWORK_TESTNET_MULTI} from "@/lib/misc";
import {addCurrency, nicePercentFormat, prettyDateFromTimestamp, volumeFormat} from "@/lib/digits";
import {shortAddress} from "@/lib/address";

export default {
    props: [
        'item',
        'network',
        'index',
        'place',
        'totalVolume',
        'currency',
        'hideValue'
    ],
    methods: {
        viewAddressInExplorer(address) {
            if (this.network === NETWORK_CHAOSNET_BEP2) {
                return 'https://viewblock.io/thorchain/address/' + address
            } else if (this.network === NETWORK_CHAOSNET_MUTLI) {
                return 'https://viewblock.io/thorchain/address/' + address
            } else if (this.network === NETWORK_TESTNET_MULTI) {
                return 'https://thorchain.net/#/address/' + address
            } else {
                return 'https://thorchain.org'
            }
        },
    },

    filters: {
        volumeFormat,
        prettyDateFromTimestamp,
        nicePercentFormat,
        shortAddress,
        addCurrency
    },
}

</script>

<style>
.fade-enter-active, .fade-leave-active {
    transition: opacity .5s;
}

.fade-enter, .fade-leave-to /* .fade-leave-active до версии 2.1.8 */
{
    opacity: 0;
}
</style>
