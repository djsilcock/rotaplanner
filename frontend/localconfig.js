import {useQuery,useQueryClient} from '@tanstack/react-query'

const localConfigDefault={
      duty:'ICU',
      configEdit:null}
  
  function useLocalConfig(){
    const queryClient=useQueryClient()
    function setConfig(val){
      queryClient.setQueryData('localconfig',val)
    }
    const uq=useQuery({queryKey:'localconfig',initialData:localConfigDefault,queryFn:()=>Promise.resolve(localConfigDefault),staleTime:Infinity,cacheTime:Infinity})
    return {
      setConfig,
      config:uq.data}
  }

  export default useLocalConfig