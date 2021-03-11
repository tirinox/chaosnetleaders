export const NETWORK_CHAOSNET_BEP2 = 'chaosnet-bep2'
export const NETWORK_CHAOSNET_MUTLI = 'chaosnet-multi'
export const NETWORK_TESTNET_MULTI = 'testnet-multi'

export function getNetworkId() {
  return process.env.VUE_APP_THOR_NETWORK
}
