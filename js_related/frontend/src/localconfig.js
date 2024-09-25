import {createQuery,useQueryClient} from '@tanstack/solid-query'

const localConfigDefault={
      duty:'ICU',
      configEdit:null}
  
  function useLocalConfig(){
    const queryClient=useQueryClient()
    function setConfig(val){
      queryClient.setQueryData(['localconfig'],val)
    }
    const query=createQuery({queryKey:()=>['localconfig'],initialData:localConfigDefault,queryFn:()=>Promise.resolve(localConfigDefault),staleTime:Infinity,cacheTime:Infinity})
    return {
      setConfig,
      config:()=>q.data}
  }

  export default useLocalConfig