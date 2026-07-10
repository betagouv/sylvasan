<script setup type="ts">

const opened = defineModel()
</script>

<template>
  <DsfrModal
    :opened="opened"
    title="Titre de page manquant"
    @close="opened = false"
  >
    <p>
      Toutes les pages doivent avoir un titre. Veuillez renseigner le titre de
      chaque page avant de sauvegarder.
    </p>
    <template #footer>
      <div class="flex justify-end w-full">
        <DsfrButton label="OK" @click="opened = false" />
      </div>
    </template>
  </DsfrModal>
</template>
