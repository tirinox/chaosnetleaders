<template lang="html">
  <div>
    <b-navbar toggleable="md" type="dark" variant="dark" class="mb-5">
      <b-navbar-brand href="#">
        <img src="/img/icons/favicon-32x32.png" class="d-inline-block align-middle nav-logo pr-2" alt="Logo">
        Chaosnet leaders
      </b-navbar-brand>

      <b-navbar-toggle target="nav-collapse"></b-navbar-toggle>

      <b-collapse id="nav-collapse" is-nav>
        <b-navbar-nav>
          <b-nav-item to="/" :active="$route.path === '/'">Leaderboard</b-nav-item>
          <b-nav-item to="/help" :active="$route.path === '/help'">Help</b-nav-item>
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

export default {
  name: 'App',
  computed: {
    packageJson() {
      return '0.1.3'
    }
  }
}
</script>

<style>
  .footer {
    padding: 5px;
  }

</style>
