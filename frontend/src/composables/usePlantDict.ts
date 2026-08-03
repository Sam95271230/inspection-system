import { ref } from 'vue'
import { getPlantDictTree } from '@/api/inspection'

export interface PlantOption {
  value: string
  label: string
  children?: any[]
}

export interface LineOption {
  value: string
  label: string
  children?: any[]
}

export interface StationOption {
  value: string
  label: string
}

export function usePlantDict() {
  const plantOptions = ref<PlantOption[]>([])
  const lineOptions = ref<LineOption[]>([])
  const stationOptions = ref<StationOption[]>([])

  const fetchDict = async () => {
    const res: any[] = await getPlantDictTree()
    plantOptions.value = res.map((p: any) => ({
      value: p.id,
      label: `${p.code} - ${p.name}`,
      children: p.children,
    }))
  }

  const onPlantChange = (plantId: string) => {
    lineOptions.value = []
    stationOptions.value = []

    const plant = plantOptions.value.find(p => p.value === plantId)
    if (plant?.children) {
      lineOptions.value = plant.children.map((l: any) => ({
        value: l.id,
        label: `${l.code} - ${l.name}`,
        children: l.children,
      }))
    }
  }

  const onLineChange = (lineId: string) => {
    stationOptions.value = []

    const line = lineOptions.value.find(l => l.value === lineId)
    if (line?.children) {
      stationOptions.value = line.children.map((s: any) => ({
        value: s.id,
        label: `${s.code} - ${s.name}`,
      }))
    }
  }

  return { plantOptions, lineOptions, stationOptions, fetchDict, onPlantChange, onLineChange }
}
