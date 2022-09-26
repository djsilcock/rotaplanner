import { configureStore, combineReducers, createReducer, createSlice } from '@reduxjs/toolkit'
import React from 'react'
import { Provider } from 'react-redux'
import { set } from 'lodash'

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import { addDays, formatISO, parseISO } from 'date-fns'

interface ConfigSlice{
  startDate: string,
  numDays: number,
  daysArray?:string[]
}
export interface StateShape{
  config: ConfigSlice,
  api
}

interface ShiftData{
  [name:string]:string
}
export interface DayData{
  [shift:string]:ShiftData
}

interface DutiesData{
  [day:string]:DayData
}
export interface GetDutiesResult{
  days: string[],
  names: string[],
  duties:DutiesData
}


// Define a service using a base URL and expected endpoints
export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({ baseUrl: '/' }),
  tagTypes:['Duties','Constraints'],
  endpoints: (builder) => ({
    getStatusMessage: builder.query({
      query: () => 'statusmessage'
    }),
    getDuties: builder.query<GetDutiesResult|undefined,ConfigSlice>({
      query: ({ startDate, numDays }) => `duties/${startDate}?days=${numDays}`,
      providesTags: ['Duties']
    }),    
    setDuty: builder.mutation({
      query: ({ date, shift, staff, duty }) => ({
        url: 'setduty',
        method: 'POST',
        body: { date, shift, staff, duty }
      }),
      invalidatesTags:['Duties'],
      async onQueryStarted({ date, shift, staff, duty }, { dispatch, getState }) {
        const state = getState() as StateShape
        const startDate = state.config.startDate
        const numDays = state.config.numDays
        dispatch(
          api.util.updateQueryData('getDuties', { startDate, numDays }, (draft) => {
            set(draft, [date, shift, staff], duty)
          })
        )
      }
    }),
    getConstraintConfig:builder.query<any,undefined>({
      query:()=>'getconstraints',
      providesTags:['Constraints']
    }),
    getConstraintInterface: builder.query({
      query: (config) => (
        {
          url: 'getconstraintinterface',
          method: 'POST',
          body: config
        })
    }),
    resetConstraintConfig:builder.mutation({
      queryFn:()=>({data:null}),
      invalidatesTags:['Constraints']
    }),
    updateConstraintConfigValue: builder.mutation({
      queryFn: () => ({ data: null }),
      onQueryStarted({ type, id, name, value }) {
        api.util.updateQueryData('getConstraintConfig', undefined, (state) => {
          (state[type]?.rules?.[id] ?? {})[name]=value
        })
      }
    }),
    addConstraintRule: builder.mutation({
      queryFn: () => ({ data: null }),
      onQueryStarted({ type}) {
        api.util.updateQueryData('getConstraintConfig', undefined, (state) => {
          const newId=Math.random().toString(36).slice(2)
          state[type].rules[newId]={id:newId}
        })
      }
    }),
    removeConstraintRule: builder.mutation({
      queryFn: (data:{type:string,id:string}) => ({ data }),
      onQueryStarted({ type, id }) {
        api.util.updateQueryData('getConstraintConfig', undefined, (state) => {
          (state?.[type]?.rules[id] ?? {}).deleted=true
        })
      }
    }),
    saveConstraints:builder.mutation({
      query:(constraints)=>({
        url:'saveconstraints',
        method:'POST',
        body:constraints
      })
    })
  }),
})

// Export hooks for usage in functional components, which are
// auto-generated based on the defined endpoints

const initialState = { numDays: 16 * 7, startDate: '2021-01-01' }

function addDaysArray(state:ConfigSlice) {
  const { numDays, startDate: startdatestr } = state
  const startDate = parseISO(startdatestr)
  state.daysArray = [...Array(numDays)].map((x, i) => formatISO(addDays(startDate, i), { representation: 'date' }))

}
const configReducer = createSlice({
  name: 'config',
  initialState: () => {
    const state = { ...initialState}
    addDaysArray(state)
    return state
  },
    reducers: {
    setStartDate(state, action) {
        state.startDate = action.payload
        addDaysArray(state)
    },
      setDaysToShow(state, action) {
        state.numDays == action.payload
        addDaysArray(state)
      },
    
  }
})
const store = configureStore({
  reducer:{config:configReducer.reducer,
      [api.reducerPath]: api.reducer
    },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(api.middleware),
  //preloadedState: window.initialData
})

export function ReduxProvider({ children }) {
  return <Provider store={store}>{children}</Provider>
}