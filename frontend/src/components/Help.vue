<template>

  <div class="row">
    <div class="col-12">
      <h1>Help / info</h1>
      <p>
        This is the leaderboard of THORChain traders.
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
      <pre>
        Prev Input Swap = Find(Previous Swap between ᚱ &lt;=&gt; This double swap input asset)
        Prev Output Swap = Find(Previous Swap between ᚱ &lt;=&gt; This double swap output asset)
        Prev Swap = What later?( (Prev Input Swap) or (Prev Output Swap) )
        ᚱ volume = (This Input or Output asset volume) / (Prev Swap ᚱ price)
      </pre>
      <h3>Change log</h3>
      <h4>v. 0.3.0</h4>
      <ul>
        <li>Multi-chain support</li>
        <li>Migration to PostreSQL</li>
      </ul>
      <h4>v. 0.2.1</h4>
      <ul>
        <li>Button style change</li>
        <li>Default mode: Last week</li>
      </ul>
      <h4>v. 0.2.0</h4>
      <ul>
        <li>New algorithm for calculating asset prices</li>
        <li>USD/RUNE switch for volume</li>
      </ul>
      <h4>v. 0.1.3</h4>
      <ul>
        <li>Competition ending date</li>
      </ul>
      <h4>v. 0.1.2</h4>
      <ul>
        <li>Fixed the fetch task fail and stop</li>
      </ul>
      <h4>v. 0.1.1</h4>
      <ul>
        <li>Small fixes</li>
      </ul>
      <h4>v. 0.1.0</h4>
      <ul>
        <li>Pagination</li>
        <li>Start date switch with competition start, all time, last month, last week, last day options</li>
      </ul>
      <h4>v. 0.0.9</h4>
      <ul>
        <li>Change log added</li>
        <li>Full sync with Midgard every 24 hours</li>
      </ul>
    </div>
  </div>

</template>

<script>

export default {

}

</script>
