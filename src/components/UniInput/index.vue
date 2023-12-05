<script lang="ts">
import './index.scss'

export default {
  name: 'UniUniInput',
  props: ['type', 'name', 'placeholder', 'modelValue'],
  computed: {
    hiddenText() {
      return typeof this.modelValue === 'string'
        ? this.modelValue.replace(/\n$/g, '<br />&nbsp;')
        : ''
    }
  },
  methods: {
    handleChange(event: Event) {
      const target = event.target as HTMLInputElement
      this.$emit('update:modelValue', target.value)
    }
  }
}
</script>

<template>
  <div class="UniInput">
    <template v-if="type === 'area'">
      <div class="UniInputElement UniInputElement_hidden" v-html="hiddenText"></div>
      <textarea
        class="UniInputElement UniInputElement_visible"
        :placeholder="placeholder"
        :value="modelValue"
        @input="handleChange"
      ></textarea>
    </template>
    <input
      v-else
      class="UniInputElement"
      :placeholder="placeholder"
      :value="modelValue"
      @input="handleChange"
    />
  </div>
</template>
