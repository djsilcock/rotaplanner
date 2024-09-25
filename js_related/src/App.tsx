import type { Component } from 'solid-js';

import MenuIcon from "@suid/icons-material/Menu";
import {
  AppBar,
  Box,
  Button,
  IconButton,
  Toolbar,
  Typography,
} from "@suid/material";

import logo from './logo.svg';
import styles from './App.module.css';
import { createMemo, createSignal,For } from 'solid-js'
import { Router,useNavigate,Route,useMatch,useLocation } from '@solidjs/router';
import Table from './table'
import { QueryClient, QueryClientProvider } from '@tanstack/solid-query';
import CalendarMonth from "@suid/icons-material/CalendarMonth";
import EditCalendar from "@suid/icons-material/Edit"
import Solve from "@suid/icons-material/AutoAwesome"
import InboxIcon from "@suid/icons-material/MoveToInbox";
import {
  Divider,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from "@suid/material";
import { DrawerProps } from "@suid/material/Drawer";
import { createMutable } from "solid-js/store";

type Anchor = NonNullable<DrawerProps["anchor"]>;

const pages=[
  {icon:CalendarMonth,title:'View rota',path:'/rota',component:Table},
  {icon:EditCalendar,title:'Edit demand templates',path:'/demand_templates',component:Templates},
  {icon:EditCalendar,title:'Edit supply templates',path:'/supply_templates',component:Templates},
  {icon:Solve,title:'Solve',path:'/solver',component:Templates}
]

function Layout(props) {
  const [open, setOpen] = createSignal(false)
  const navigator=useNavigate()
  const match=useLocation()
  const title=createMemo(()=>pages?.find(page=>page.path==match.pathname)?.title??"")
  return (
    <div>
      <Drawer
        anchor='left'
        open={open()}
        sx={{ zIndex: 9999 }}
        onClose={() => setOpen(false)}
      >
        <List>
          <For each={pages}>{({icon:ItemIcon,title,path})=><ListItem disablePadding onClick={()=>{navigator(path);setOpen(false)}}>
              <ListItemButton>
                <ListItemIcon>
                  <ItemIcon/>
                </ListItemIcon>
                <ListItemText primary={title} />
              </ListItemButton>
            </ListItem>}</For>
          
        </List>
        <Divider />
        
      </Drawer>

      <AppBar position="static">
        <Toolbar>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="menu"
            sx={{ mr: 2 }}
            onClick={()=>setOpen((val)=>!val)}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            {title()}
          </Typography>
          <Button color="inherit">Login</Button>
        </Toolbar>
      </AppBar>
      <div class={styles.App}>
        {props.children}
      </div>
    </div>
  );
}

function Templates(){
  return <h1>TBA</h1>
}
const client = new QueryClient()
const App: Component = () => {
  return (
    <QueryClientProvider client={client}>
      <Router root={Layout}>{pages}</Router>
    </QueryClientProvider>
  );
};

export default App;

