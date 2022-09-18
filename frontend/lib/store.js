import { configureStore, combineReducers } from '@reduxjs/toolkit'
import React from 'react'
import { io } from 'socket.io-client'
import { Provider } from 'react-redux'
import { constraintsReducer } from '../components/settingsRedux'
import { createApi } from '@reduxjs/toolkit/query/react'
import { set } from 'lodash'

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

// Define a service using a base URL and expected endpoints
export const dutiesApi = createApi({
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
      async onQueryStarted({ date, shift, staff, duty }, { dispatch, getState, queryFulfilled }) {
        const state = getState()
        const startdate = state.config.startdate
        const days = state.config.daysToShow
        dispatch(
          api.util.updateQueryData('getDuties', { startdate, days }, (draft) => {
            set(draft, [date, shift, staff], duty)
          })
        )
        try {
          await queryFulfilled
        } catch { }
        api.util.invalidateTags(['Duties'])
      }
    }),
    getConstraintConfig:builder.query({
      query:()=>'getconstraints',
      providesTags:['Constraints']
    }),
    resetConstraintConfig:builder.mutation({
      queryFn:()=>({data:null}),
      invalidatesTags:['Constraints']
    }),
    validateConstraint:builder.mutation({
      query:(data)=>({
        url:'validateconstraint',
        method:'POST',
        body:data
      }),
      async onQueryStarted (_,{queryFulfilled}){
        try{
          const {data:{constraintType,constraintId,...data}}=await queryFulfilled
          api.util.updateQueryData('getConstraintConfig',undefined,(config)=>{
            set(config,[constraintType,constraintId],data)
          })
        }catch{}
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
export const { useGetDutiesQuery } = dutiesApi
const socket = io()
const store = configureStore({
  reducer: combineReducers(
    {
      config: combineReducers({ constraints: constraintsReducer }),
      [dutiesApi.reducerPath]: dutiesApi.reducer
    }),
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(pokemonApi.middleware),
  preloadedState: window.initialData
})
socket.on("connect", () => socket.emit("reset_state", decodeAndDispatch));
socket.on("dispatch", store.dispatch);

export function ReduxProvider({ children }) {
  return <Provider store={store}>{children}</Provider>
}