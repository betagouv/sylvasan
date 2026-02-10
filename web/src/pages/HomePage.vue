<route lang="json">
{
  "path": "/accueil",
  "meta": {
    "title": "Accueil"
  }
}
</route>

<script setup lang="ts">
import imgUrl from "../../public/forest.jpg"
import backgroundUrl from "../../public/leaves.png"
import ImageAttribution from "../components/ImageAttribution.vue"
import { useRootStore } from "../stores/root"
import { storeToRefs } from "pinia"

const store = useRootStore()
const { loggedUser } = storeToRefs(store)
</script>

<template>
  <div class="">
    <div class="bg-blue-france-975 relative inset-shadow-sm">
      <img
        class="hidden md:block absolute w-64 opacity-25 top-0 right-0 md:right-0 lg:right-10 xl:right-50"
        :src="backgroundUrl"
        alt=""
      />
      <div
        class="relative fr-container py-6 sm:py-10 md:py-12 grid grid-cols-12"
      >
        <div class="col-span-12 md:col-span-8 lg:col-span-6">
          <h1>La santé des forêts, relevée et suivie collectivement</h1>
          <p>
            Votre plateforme dédiée au diagnostic et suivi sanitaire de la forêt
          </p>
          <router-link
            :to="{ name: '/LoginPage' }"
            class="fr-btn fr-btn--md mt-4"
            v-if="loggedUser"
          >
            Aller au tableau de bord
          </router-link>
          <router-link
            :to="{ name: '/LoginPage' }"
            class="fr-btn fr-btn--md mt-4"
            v-else
          >
            S'identifier
          </router-link>
        </div>
      </div>
    </div>
    <div class="fr-container my-10">
      <div class="grid grid-cols-12 gap-8">
        <div class="hidden sm:block sm:col-span-6 md:col-span-4">
          <img :src="imgUrl" alt="forêt" class="rounded-md max-h-80" />
          <ImageAttribution
            licenseName="CC BY 2.0"
            licenseUrl="https://creativecommons.org/licenses/by/2.0/?ref=openverse"
            sourceUrl="https://www.flickr.com/photos/38436453@N07/3924238584"
            author="targut"
            authorUrl="https://www.flickr.com/photos/38436453@N07"
            :creativeCommons="true"
          />
        </div>
        <div class="col-span-12 sm:col-span-6 md:col-span-8">
          <h2>Notre mission</h2>
          <p class="font-bold">
            Faciliter le relevé et le suivi des problèmes sanitaires des arbres
            en forêt
          </p>
          <p>
            SylvaSan vise à aider le DSF (Département Santé des Forêts) dans sa
            mission d’animer un réseau de forestiers en territoires qui se sont
            portés volontaires pour surveiller l’émergence et l’évolution des
            maladies des arbres en forêt.
          </p>
          <p>Ce produit est en construction.</p>
        </div>
      </div>
    </div>
  </div>
</template>
