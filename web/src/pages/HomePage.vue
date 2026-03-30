<route lang="json">
{
  "path": "/accueil",
  "meta": {
    "title": "Accueil"
  }
}
</route>

<script setup lang="ts">
import imgUrl from "../assets/forest.jpg"
import backgroundUrl from "../assets/leaves.png"
import ImageAttribution from "../components/ImageAttribution.vue"
</script>

<template>
  <div>
    <div class="bg-blue-france-975 relative inset-shadow-sm">
      <img
        class="hidden md:block absolute w-60 opacity-25 top-0 right-0 md:right-0 lg:right-10 xl:right-50"
        :src="backgroundUrl"
        alt=""
      />
      <div
        class="relative fr-container py-6 sm:py-10 md:py-12 grid grid-cols-12"
      >
        <div class="col-span-12 md:col-span-8 lg:col-span-6">
          <h1>SylvaSan</h1>
          <p>
            L'application de relevé et de suivi des problèmes sanitaires des
            arbres en forêt
          </p>

          <a
            href="https://beta.gouv.fr/startups/sylva-san.html"
            rel="noopener external"
            class="fr-btn fr-btn--secondary fr-btn--md mt-4"
          >
            En savoir plus
          </a>
        </div>
      </div>
    </div>
    <div class="fr-container pt-12 pb-6">
      <div class="grid grid-cols-12 gap-8">
        <div class="hidden lg:block lg:col-span-4">
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
        <div class="col-span-12 lg:col-span-8">
          <h2>La forêt française face à une crise sans précédent</h2>

          <p>
            La situation de la forêt est critique. La situation sanitaire des
            forêts s’aggrave rapidement sous l’effet du changement climatique et
            de la mondialisation. Les effets sont de plus en plus visibles :
            sécheresses, tempêtes, accélération du dépérissement et des nouveaux
            organismes exotiques.
          </p>
          <ul>
            <li>
              <span class="font-bold"
                >De 300k ha à 1M ha de forêts dépérissantes</span
              >
              entre 2017 et 2023
            </li>
            <li>
              <span class="font-bold">+80% de mortalité</span> des arbres en 10
              ans
            </li>
            <li>
              <span class="font-bold">600% nouveaux organismes</span> exotiques
              ces 20 dernières années
            </li>
          </ul>
        </div>
      </div>
    </div>
    <div class="bg-blue-france-975 py-8">
      <div class="fr-container">
        <h2>Notre mission</h2>

        <p>
          Participer à la lutte contre le dépérissement en facilitant les
          actions des pouvoirs publics et des chercheurs grâce à des données
          réactives et fiables.
        </p>
      </div>
    </div>
    <div class="fr-container py-8">
      <h2>La solution SylvaSan</h2>

      <p>
        SylvaSan est une application mobile destinée aux forestiers du
        Département de la santé des forêts qui vise à sécuriser et encourager la
        signalisation des symptômes en forêt.
      </p>
      <p>Elle permet de :</p>
      <ul>
        <li>Faciliter le relevé des problèmes sanitaires en forêt</li>
        <li>Faciliter le diagnostic in-situ</li>
        <li>Centraliser l’ensemble des enquêtes</li>
        <li>Augmenter la réactivité en cas de crise sanitaire.</li>
      </ul>
      <p class="py-4">
        ℹ️ <span class="italic">Ce produit est en cours de construction</span>
      </p>
      <hr />
      <h2 class="fr-h4">Le Département de la Santé des Forêts</h2>
      <p>
        Le Département de la santé des forêts (DSF) détecte, comprend et
        anticipe les menaces sanitaires qui pèsent sur la forêt, pour
        accompagner une gestion forestière plus résiliente face au climat et aux
        bioagresseurs. Le DSF, c’est 15 000 observations sylvosanitaires par an.
      </p>
      <p>
        Le DSF mène sa mission en se basant sur les signalements récoltés sur le
        terrain par un réseau national de forestiers volontaires, qu'il forme à
        la détection des problèmes sanitaires, et anime en continu. Les données
        sont ensuite mises à disposition des pouvoirs publics, gestionnaires et
        chercheurs.
      </p>
    </div>
  </div>
</template>
