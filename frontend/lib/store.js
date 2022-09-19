import { configureStore, combineReducers } from '@reduxjs/toolkit'
import React from 'react'
import { Provider } from 'react-redux'
import { set } from 'lodash'

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

// Define a service using a base URL and expected endpoints
export const api = createApi({
  reducerPath: 'remote',
  baseQuery: fetchBaseQuery({ baseUrl: '/' }),
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
    getConstraintConfig:builder.query({
      query:()=>'getconstraints',
      providesTags:['Constraints']
    }),
    getConstraintInterface:builder.query({
      query:(config)=>(
        {url:'getconstraintinterface',
        method:'POST',
        body:config
    }),
    resetConstraintConfig:builder.mutation({
      queryFn:()=>({data:null}),
      invalidatesTags:['Constraints']
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
})
// Export hooks for usage in functional components, which are
// auto-generated based on the defined endpoints

const store = configureStore({
  reducer: combineReducers(
    {
      [api.reducerPath]: api.reducer
    }),
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(api.middleware),
  preloadedState: window.initialData
})

export function ReduxProvider({ children }) {
  return <Provider store={store}>{children}</Provider>
}