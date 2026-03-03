<route lang="json">
{
  "path": "/a11y",
  "meta": {
    "title": "Accessibilité"
  }
}
</route>

<script setup lang="ts"></script>

<template>
  <div class="fr-container mb-10">
    <DsfrBreadcrumb
      :links="[{ to: '/', text: 'Accueil' }, { text: 'Accessibilité' }]"
    />
    <h1>Déclaration d'accessibilité</h1>
    <p>
      SylvaSan s’engage à rendre ses applications accessibles conformément à
      l’article 47 de la loi n°2005-102 du 11 février 2005.
    </p>
    <p>
      À cette fin, SylvaSan met en œuvre la stratégie et les actions suivantes :
    </p>
    <ul>
      <li>L'usage des composants et éléments UI accessibles</li>
      <li>
        La réalisation d’un audit RGAA par un prestataire spécialisé (prévue en
        fin de construction)
      </li>
      <li>La publication d’une déclaration d’accessibilité officielle</li>
      <li>La correction des non-conformités identifiées</li>
    </ul>
    <p>Cette déclaration d’accessibilité s’applique à sylvasan.beta.gouv.fr.</p>
    <h2>État de conformité</h2>
    <p>
      Sylvasan est <span class="font-bold">non conforme</span> avec le
      référentiel général d’amélioration de l’accessibilité (RGAA), version 4.
      Sylvasan est dans l’attente d’une évaluation formelle et d'un audit
      d’accessibilité complet.
    </p>
    <h2>Établissement de cette déclaration d’accessibilité</h2>
    <p>Cette déclaration a été établie le 3 mars 2026.</p>
    <h2>Technologies utilisées pour la réalisation du site</h2>
    <ul>
      <li>Vue JS</li>
      <li>DSFR</li>
    </ul>
    <h2>Voies de recours</h2>
    <p>
      Si vous constatez un défaut d’accessibilité vous empêchant d’accéder à un
      contenu ou une fonctionnalité du site, que vous nous le signalez et que
      vous ne parvenez pas à obtenir une réponse de notre part, vous êtes en
      droit de faire parvenir vos doléances ou une demande de saisine au
      Défenseur des droits.
    </p>
    <p>Plusieurs moyens sont à votre disposition :</p>
    <ul>
      <li>Écrire un message au Défenseur des droits</li>
      <li>Contacter le délégué du Défenseur des droits dans votre région</li>
      <li>
        Envoyer un courrier par la poste (gratuit, ne pas mettre de timbre) :<br />
        Défenseur des droits<br />
        Libre réponse 71120<br />
        75342 Paris CEDEX 07
      </li>
    </ul>
  </div>
</template>
