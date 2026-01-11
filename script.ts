import * as BunnySDK from "https://esm.sh/@bunny.net/edgescript-sdk@0.11.2";

BunnySDK.net.http.serve(async (request: Request): Promise<Response> => {
  return new Response("Hello World");
});
