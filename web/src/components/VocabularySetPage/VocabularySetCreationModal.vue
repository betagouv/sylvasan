<script setup lang="ts">
import * as z from "zod"
import { ref, computed } from "vue"
import { ZodError } from "zod"
import { useRouter } from "vue-router"
import { useApiFetch } from "../../utils/data-fetching"
import { useToastStore } from "../../stores/toast"
import { useRootStore } from "../../stores/root"

defineProps<{ opened: boolean }>()
const emit = defineEmits<{ close: [] }>()

const router = useRouter()
const toast = useToastStore()
const rootStore = useRootStore()

const adminOrgs = computed(() => {
  const seen = new Set<number>()
  return (
    rootStore.loggedUser?.memberships
      .filter((m) => m.membershipType === "admin")
      .filter((m) => {
        if (seen.has(m.organisation.id)) return false
        seen.add(m.organisation.id)
        return true
      })
      .map((m) => ({
        value: String(m.organisation.id),
        text: m.organisation.name,
      })) ?? []
  )
})

const payload = ref({ code: "", name: "", organisation: "" })

const validator = z.object({
  code: z.string().min(1, "Le code est obligatoire"),
  name: z.string().min(1, "Le nom est obligatoire"),
  organisation: z.string().min(1, "L'organisation est obligatoire"),
})

const formErrors = ref<{
  formErrors: string[]
  fieldErrors: Record<string, string[]>
}>({ formErrors: [], fieldErrors: {} })

const clearFieldError = (field: string) => {
  if (formErrors.value.fieldErrors[field])
    delete formErrors.value.fieldErrors[field]
}

const { execute, isFetching, statusCode, data } = useApiFetch(
  "/admin/vocabularies/",
  {
    immediate: false,
  }
)
  .post(
    computed(() => ({
      ...payload.value,
      organisation: payload.value.organisation
        ? Number(payload.value.organisation)
        : null,
    }))
  )
  .json()

const onClose = () => {
  payload.value = { code: "", name: "", organisation: "" }
  formErrors.value = { formErrors: [], fieldErrors: {} }
  emit("close")
}

const onSubmit = async () => {
  formErrors.value = { formErrors: [], fieldErrors: {} }
  try {
    validator.parse(payload.value)
  } catch (error) {
    if (error instanceof ZodError) formErrors.value = z.flattenError(error)
    return
  }
  await execute()
  if (statusCode.value === 201) {
    toast.show("Le référentiel a été créé.", "success")
    emit("close")
    rootStore.refreshVocabularies()
    router.push({
      name: "/VocabularySetDetailPage",
      params: { id: data.value.id },
    })
  } else {
    toast.show("Une erreur s'est produite.", "error")
  }
}
</script>

<template>
  <DsfrModal :opened="opened" title="Créer un référentiel" @close="onClose">
    <form @submit.prevent="onSubmit">
      <DsfrInputGroup :error-message="formErrors.fieldErrors.code?.[0]">
        <DsfrInput
          v-model="payload.code"
          label="Code"
          hint="Ce code doit être unique dans votre organisation"
          label-visible
          :required="true"
          @update:model-value="clearFieldError('code')"
        />
      </DsfrInputGroup>
      <DsfrInputGroup :error-message="formErrors.fieldErrors.name?.[0]">
        <DsfrInput
          v-model="payload.name"
          label="Nom"
          hint="Ajoutez un titre descriptif court"
          label-visible
          :required="true"
          @update:model-value="clearFieldError('name')"
        />
      </DsfrInputGroup>
      <DsfrInputGroup :error-message="formErrors.fieldErrors.organisation?.[0]">
        <DsfrSelect
          v-model="payload.organisation"
          label="Organisation"
          :options="[
            { value: '', text: 'Sélectionner une organisation' },
            ...adminOrgs,
          ]"
          @update:model-value="clearFieldError('organisation')"
        />
      </DsfrInputGroup>
    </form>
    <p>
      <v-icon name="ri-information-line" scale="1.2" />
      Vous pourrez ajouter des entrées dans la prochaine étape
    </p>
    <template #footer>
      <div class="flex justify-end gap-2 w-full">
        <DsfrButton label="Annuler" secondary @click="onClose" />
        <DsfrButton
          label="Créer"
          icon="ri-add-line"
          :disabled="isFetching"
          @click="onSubmit"
        />
      </div>
    </template>
  </DsfrModal>
</template>
