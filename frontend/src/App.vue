<template lang="html">
  <div>
    <b-navbar toggleable="md" type="dark" variant="dark" class="mb-5">
      <b-navbar-brand href="#">Chaosnet</b-navbar-brand>

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
        <span class="text-muted">This is an alpha version 0.0.1!</span>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
  .footer {
    padding: 5px;
  }
</style>
