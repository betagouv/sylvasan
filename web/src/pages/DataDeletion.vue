<route lang="json">
{
  "path": "/suppression-donnees",
  "meta": {
    "title": "Suppression données personnelles"
  }
}
</route>

<script setup lang="ts"></script>

<template>
  <div class="fr-container mb-10">
    <DsfrBreadcrumb
      :links="[
        { to: '/', text: 'Accueil' },
        { text: 'Suppression des données personnelles' },
      ]"
    />
    <h1>Suppression des données personnelles — SylvaSan</h1>

    <p>
      Conformément au Règlement Général sur la Protection des Données (RGPD),
      vous disposez du droit de demander la suppression de votre compte SylvaSan
      ainsi que de l'ensemble des données personnelles associées.
    </p>

    <h2>Comment faire une demande de suppression</h2>

    <p>
      Pour demander la suppression de votre compte et de vos données, envoyez un
      e-mail à :
    </p>
    <p class="font-bold">contact [at] sylvasan.beta.gouv.fr</p>

    <p>Votre e-mail doit contenir les informations suivantes :</p>
    <ul>
      <li>l'adresse e-mail associée à votre compte SylvaSan ;</li>
      <li>l'objet : <strong>Demande de suppression de compte</strong> ;</li>
      <li>toute précision utile permettant de vous identifier.</li>
    </ul>

    <p>
      Nous traiterons votre demande dans un délai maximum de
      <strong>30 jours</strong>
      à compter de sa réception et vous enverrons une confirmation par e-mail.
    </p>

    <h2>Données supprimées</h2>

    <p>Suite à votre demande, les données suivantes seront supprimées :</p>
    <ul>
      <li>votre compte (nom, prénom, adresse e-mail, nom d'utilisateur) ;</li>
      <li>vos données personnelles ;</li>
    </ul>

    <h2>Données conservées</h2>

    <p>
      Certaines données peuvent être conservées au-delà de la suppression du
      compte pour répondre à des obligations légales ou à des finalités
      d'intérêt public :
    </p>
    <ul>
      <li>
        les données d'hébergeur et de connexion sont conservées conformément à
        la loi LCEN n° 2004-575 du 21 juin 2004 et au décret n° 2021-1363 du 20
        octobre 2021 (durée légale : 1 an) ;
      </li>
      <li>
        les données statistiques et agrégées issues des enquêtes, rendues
        anonymes, peuvent être conservées à des fins de suivi sanitaire
        forestier.
      </li>
    </ul>
  </div>
</template>
