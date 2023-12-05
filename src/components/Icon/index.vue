<script lang="ts">
import './index.scss'

export default {
  name: 'Icon',
  props: ['name']
}
</script>

<template>
  <span class="Icon" :class="['Icon-' + name]">
    <svg class="IconSvg">
      <use :href="'#icon-' + name" />
    </svg>
  </span>
</template>
