<template lang="html">
  <div>
    <b-navbar toggleable="md" type="dark" variant="dark" class="mb-5">
      <b-navbar-brand href="#">
        <img src="/img/icons/favicon-32x32.png" class="d-inline-block align-middle nav-logo pr-2" alt="Logo">
        {{ site_title }}
      </b-navbar-brand>

      <b-navbar-toggle target="nav-collapse"></b-navbar-toggle>

      <b-collapse id="nav-collapse" is-nav>
        <b-navbar-nav>
          <b-nav-item to="/" :active="$route.path === '/'">Leaderboard</b-nav-item>
          <b-nav-item to="/help" :active="$route.path === '/help'">Help</b-nav-item>
        </b-navbar-nav>

        <b-nav-form class="ml-4">
          <b-form-radio-group
            button-variant="success"
            v-model="selected"
            :options="currencyOptions"
            name="buttons-1"
            buttons
            @change="on_currency_switch"
          ></b-form-radio-group>
        </b-nav-form>
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

import { ON_CURRENCY_CHANGE, EventBus } from '@/lib/bus'

export default {
  name: 'App',
  data () {
    return {
      selected: 'rune',
      site_title: 'Chaosnet leaders'
    }
  },
  methods: {
    on_currency_switch(v) {
      EventBus.$emit(ON_CURRENCY_CHANGE, v)
    }
  },
  computed: {
    currencyOptions () {
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
    packageJson () {
      console.log(' process.env = ',  process.env)
      return process.env.VUE_APP_VERSION || '0'
    }
  }
}
</script>

<style>
.footer {
  padding: 5px;
}

</style>
