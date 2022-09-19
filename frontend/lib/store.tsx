import { configureStore, combineReducers, createReducer, createSlice } from '@reduxjs/toolkit'
import React from 'react'
import { Provider } from 'react-redux'
import { set } from 'lodash'

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

// Define a service using a base URL and expected endpoints
export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({ baseUrl: '/' }),
  tagTypes:['Duties','Constraints'],
  endpoints: (builder) => ({
    getStatusMessage: builder.query({
      query: () => 'statusmessage'
    }),
    getDuties: builder.query({
      query: ({ startdate, days }) => `duties/${startdate}?days=${days}`,
      providesTags: ['Duties']
    }),    
    setDuty: builder.mutation({
      query: ({ date, shift, staff, duty }) => ({
        url: 'setduty',
        method: 'POST',
        body: { date, shift, staff, duty }
      }),
      invalidatesTags:['Duties'],
      async onQueryStarted({ date, shift, staff, duty }, { dispatch, getState}) {
        const state = getState()
        const startdate = state.config.startdate
        const days = state.config.daysToShow
        dispatch(
          api.util.updateQueryData('getDuties', { startdate, days }, (draft) => {
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
          (state.find(item => item.type == type)
            ?.rules
            ?.find(item => item.id == id) ?? {})[name]=value
        })
      }
    }),
    addConstraintRule: builder.mutation({
      queryFn: () => ({ data: null }),
      onQueryStarted({ type}) {
        api.util.updateQueryData('getConstraintConfig', undefined, (state) => {
          (state.find(item => item.type == type) || { rules: [] })
            .rules.push({ id: Math.random().toString(36).slice(2) })
        })
      }
    }),
    removeConstraintRule: builder.mutation({
      queryFn: (data:{type:string,id:string}) => ({ data:null }),
      onQueryStarted({ type, id }) {
        api.util.updateQueryData('getConstraintConfig', undefined, (state) => {
          (state.find(item => item.type == type) || { rules: [] })
            .rules.push({ id: Math.random().toString(36).slice(2) })
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
const configReducer = createSlice({
  name: 'config',
  initialState:{daysToShow:16*7,startdate:'2021-01-01'},
  reducers: {
    setStartDate(state, action) { state.startdate = action.payload },
    setDaysToShow(state,action){state.daysToShow==action.payload}
  }
})
const store = configureStore({
  reducer: combineReducers(
    {config:configReducer.reducer,
      [api.reducerPath]: api.reducer
    }),
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(api.middleware),
  preloadedState: window.initialData
})

export function ReduxProvider({ children }) {
  return <Provider store={store}>{children}</Provider>
}