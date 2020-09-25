<template>

  <div class="row">
    <div class="col-12">
      <h1>Help / info</h1>
      <p>
        A leaderboard for current BEPSwap trading accounts.
        The winners of the BEPSwap trading competition will be
        <a href="https://t.me/thorchain/644" target="_blank" title="Proof">based off</a> this leaderboard.
        <br>
        Learn more: <a href="https://medium.com/thorchain/bepswap-trading-competition-c74685878340" target="_blank">
          BEPSwap trading competition
        </a>.
      </p>
      <p>
        This is a tool built by a community member. Source code is available on
        <a href="https://github.com/tirinox/chaosnetleaders" target="_blank">GitHub</a>.
        <br>
        Feel free to audit the code.
      </p>
      <h4>Method</h4>
      <p>
        All the data is taken from the public
        <a href="https://midgard.bepswap.com/v1/doc" target="_blank">Midgard interface</a>.
        <br>
        Total volume for each address is counted in ᚱ
        <a href="https://www.coingecko.com/en/coins/thorchain" target="_blank">($RUNE)</a>.
        Every <em>60 seconds</em> a sync code is run to get all the latest transactions from Midgard.
        For each transaction, the ᚱ volume field is calculated. Then all ᚱ volumes are summed up and grouped by input addresses.
        Finally, the addresses are ranked based on total ᚱ volume.
      </p>
      <h4>Swap</h4>
      <p>
        For a simple swap, the input or output side amount is considered, which side is in ᚱ.
      </p>
      <h4>Double swap</h4>
      <p>For a double swap, neither side is ᚱ.
        Therefore there is a task to obtain a historical price of ᚱ at the moment of the swap.
        It is solved by scanning backwards the transaction log in time and searching for the latest moment of a simple swap
        between ᚱ and the input or output asset of the double swap mentioned before.
      </p>
      <pre>ᚱ volume = (Asset volume) / (ᚱ price)</pre>
    </div>
  </div>

</template>

<script>

export default {

}

</script>
