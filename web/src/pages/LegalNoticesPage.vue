<route lang="json">
{
  "path": "/mentions-legales",
  "meta": {
    "title": "Mentions légales"
  }
}
</route>

<script setup lang="ts"></script>

<template>
  <div class="fr-container mb-10">
    <DsfrBreadcrumb
      :links="[{ to: '/', text: 'Accueil' }, { text: 'Mentions légales' }]"
    />
    <h1>Mentions Légales</h1>
    <h2>Éditeur de la Plateforme</h2>
    <p>
      La Plateforme SylvaSan est éditée par la Ruche numérique - l'Incubateur du
      Ministère de l'Agriculture, de l'Agro-alimentaire et de la Souveraineté
      alimentaire.
    </p>
    <h2>Coordonnées</h2>
    <p>Adresse : 78 Rue de Varenne, 75007 Paris</p>
    <p>SIRET : 11007001800012</p>
    <p>SIREN : 110 070 018</p>
    <h2>Directeur de la publication</h2>
    <address>
      <p>
        Ministère de l'Agriculture, de l'Agro-alimentaire et de la Souveraineté
        alimentaire
        <br />
        Département de la Santé des Forêts
        <br />
        251 rue de Vaugirard 75732 Paris Cedex 15
      </p>
    </address>
    <h2>Hébergement de la Plateforme</h2>
    <p>Ce site est hébergé en propre par:</p>
    <address>
      <p>Clevercloud, 3 rue de l'Allier, 44000 Nantes, France.</p>
    </address>
    <h2>Accessibilité</h2>
    <p>
      La conformité aux normes d’accessibilité numérique est un objectif
      ultérieur dans le développement itératif de la plateforme. Nous nous
      efforçons de créer un maximum de composants partagés et de les rendre
      accessibles à toutes et tous.
    </p>
    <p>
      Pour en savoir plus :
      <router-link :to="{ name: '/A11yPage' }"
        >notre déclaration d'accessibilité</router-link
      >
    </p>
    <p>
      Pour nous signaler des problèmes ou suggestions d'amélioration concernant
      l'accessibilité de la plateforme, deux options :
    </p>
    <ul>
      <li>
        nous signaler par email :
        <a :href="`mailto:contact@sylvasan.beta.gouv.fr`" class="fr-link">
          contact@sylvasan.beta.gouv.fr
        </a>
      </li>
      <li>
        créer une “issue” sur le
        <a
          href="https://github.com/betagouv/sylvasan/"
          target="_blank"
          rel="noopener external"
          class="fr-link"
          title="depôt Github - nouvelle fenêtre"
          >dépôt de code sur GitHub</a
        >
      </li>
    </ul>
    <p>
      Le code source est ouvert et les contributions sont bienvenues.
      <ExternalLink
        href="https://github.com/betagouv/sylvasan/"
        text="Voir le code source"
      />
    </p>
    <h2>Données personnelles, suivi d’audience et gestion des cookies</h2>
    <p>
      Le cookie est un petit fichier texte enregistré par le navigateur de votre
      ordinateur, tablette ou smartphone et qui permet de conserver des données
      utilisateur afin de faciliter la navigation et de permettre certaines
      fonctionnalités.
    </p>
    <h3>A quoi nous servent-ils ?</h3>
    <p>
      Cela nous permet de mesurer le nombre de visites et de comprendre quelles
      sont les pages les plus consultées.
    </p>
    <h3>
      Ce site n’affiche pas de bannière de consentement aux cookies, pourquoi ?
    </h3>
    <p>
      C’est vrai, vous n’avez pas eu à cliquer sur un bloc qui recouvre la
      moitié de la page pour dire que vous êtes d’accord avec le dépôt de
      cookies.
    </p>
    <p>
      Rien d’exceptionnel, pas de passe-droit lié à un .gouv.fr. Nous respectons
      simplement la loi, qui dit que certains outils de suivi d’audience,
      correctement configurés pour respecter la vie privée, sont exemptés
      d’autorisation préalable.
    </p>
    <p>
      Nous utilisons pour cela Matomo, un outil libre, paramétré pour être en
      conformité avec la recommandation « Cookies » de la CNIL. Cela signifie
      que votre adresse IP, par exemple, est anonymisée avant d’être
      enregistrée. Il est donc impossible d’associer vos visites sur ce site à
      votre personne.
    </p>
  </div>
</template>
