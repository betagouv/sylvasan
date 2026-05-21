<script setup lang="ts">
import { ref, watch } from "vue"
import type {
  Condition,
  ConditionOperator,
  LogicalOperator,
  SimpleCondition,
} from "@shared-types/survey"

const emit = defineEmits<{
  "update:modelValue": [value: Condition | undefined]
}>()

const props = defineProps<{
  fieldIds?: string[]
}>()

type ConditionRow = {
  id: string
  field: string
  operator: ConditionOperator
  valueRaw: string
}

const conditionRows = ref<ConditionRow[]>([])
const logicalOperator = ref<LogicalOperator>("and")

const operatorOptions = [
  { text: "est égal à (=)", value: "eq" },
  { text: "est différent de (≠)", value: "neq" },
  { text: "contient (multi-sélection)", value: "contains" },
  { text: "ne contient pas (multi-sélection)", value: "not_contains" },
]

const logicalOperatorOptions = [
  { label: "ET — toutes les conditions", value: "and" },
  { label: "OU — au moins une condition", value: "or" },
]

const parseConditionValue = (raw: string): unknown => {
  if (raw === "true") return true
  if (raw === "false") return false
  if (raw === "null") return null
  const n = Number(raw)
  if (raw.trim() !== "" && !isNaN(n)) return n
  return raw
}

const syncCondition = () => {
  if (conditionRows.value.length === 0) {
    emit("update:modelValue", undefined)
    return
  }
  const simple: SimpleCondition[] = conditionRows.value.map((r) => ({
    field: r.field,
    operator: r.operator,
    value: parseConditionValue(r.valueRaw),
  }))
  emit(
    "update:modelValue",
    simple.length === 1
      ? simple[0]
      : { operator: logicalOperator.value, conditions: simple }
  )
}

watch(conditionRows, syncCondition, { deep: true })
watch(logicalOperator, syncCondition)

const addConditionRow = () =>
  conditionRows.value.push({
    id: crypto.randomUUID(),
    field: "",
    operator: "eq",
    valueRaw: "",
  })

const removeConditionRow = (idx: number) => conditionRows.value.splice(idx, 1)

const serializeConditionValue = (value: unknown): string => {
  if (value === true) return "true"
  if (value === false) return "false"
  if (value === null) return "null"
  return String(value)
}

const reset = () => {
  conditionRows.value = []
  logicalOperator.value = "and"
}

const loadCondition = (condition: Condition | undefined) => {
  if (!condition) {
    reset()
    return
  }
  if ("conditions" in condition) {
    logicalOperator.value = condition.operator
    conditionRows.value = condition.conditions.map((c) => ({
      id: crypto.randomUUID(),
      field: (c as SimpleCondition).field,
      operator: (c as SimpleCondition).operator,
      valueRaw: serializeConditionValue((c as SimpleCondition).value),
    }))
  } else {
    logicalOperator.value = "and"
    conditionRows.value = [
      {
        id: crypto.randomUUID(),
        field: condition.field,
        operator: condition.operator,
        valueRaw: serializeConditionValue(condition.value),
      },
    ]
  }
}

defineExpose({ reset, loadCondition })
</script>

<template>
  <section class="mb-4">
    <h6 class="fr-text--md mb-2!">Condition d'affichage</h6>

    <DsfrRadioButtonSet
      v-if="conditionRows.length > 1"
      name="logical-operator"
      :options="logicalOperatorOptions"
      :model-value="logicalOperator"
      :inline="true"
      @update:model-value="(v: LogicalOperator) => { logicalOperator = v }"
      class="mb-3"
    />

    <div
      v-for="(row, idx) in conditionRows"
      :key="row.id"
      class="flex gap-3 items-end mb-3 border border-gray-300 px-4 pt-2 mt-2 rounded"
    >
      <DsfrSelect
        v-if="props.fieldIds?.length"
        label="Champ"
        :options="props.fieldIds.map((id) => ({ text: id, value: id }))"
        :model-value="row.field"
        @update:model-value="(v: string) => (row.field = v)"
      />
      <DsfrInputGroup v-else class="mb-0! grow">
        <DsfrInput
          label-visible
          label="Id du champ"
          v-model="row.field"
          placeholder="id_du_champ"
        />
      </DsfrInputGroup>
      <DsfrSelect
        label="Opérateur"
        :options="operatorOptions"
        :model-value="row.operator"
        @update:model-value="(v: ConditionOperator) => (row.operator = v)"
        class="shrink-0"
      />
      <DsfrInputGroup class="mb-0! grow">
        <DsfrInput
          label-visible
          label="Valeur"
          v-model="row.valueRaw"
          placeholder="true, false, null, texte, 42…"
        />
      </DsfrInputGroup>
      <div class="grow"></div>
      <div class="self-center">
        <DsfrButton
          tertiary
          icon-only
          icon="ri-delete-bin-line"
          label="Supprimer la condition"
          @click.stop="() => removeConditionRow(idx)"
        />
      </div>
    </div>

    <DsfrButton
      tertiary
      size="sm"
      icon="ri-add-line"
      :label="
        conditionRows.length === 0
          ? 'Ajouter une condition d\'affichage'
          : 'Ajouter une condition'
      "
      @click="addConditionRow"
    />
  </section>
</template>
