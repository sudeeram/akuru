import { sites } from '@openai/sites-vite-plugin';
import tailwindcss from '@tailwindcss/postcss';
import vinext from 'vinext';
import { defineConfig } from 'vite';
import { localApi } from './local-server/api.mjs';
export default defineConfig({
 css:{postcss:{plugins:[tailwindcss()]}},
 server:{host:'127.0.0.1',port:5180,strictPort:true,watch:{useFsEvents:false,usePolling:true}},
 plugins:[localApi(),vinext(),sites()],
});
