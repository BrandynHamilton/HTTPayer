const fs = require("fs");
const path = require("path");
const { ethers } = require("ethers");
require("dotenv").config();

const provider = new ethers.JsonRpcProvider(process.env.RPC_URL);
const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
const contractAddress = process.env.CONSUMER_ADDRESS;
const abi = require("../abi/HttPayerChainlinkConsumer.json");

const contract = new ethers.Contract(contractAddress, abi, wallet);

const args = [
    "http://provider.akash-palmito.org:30862/base-weather",
    "GET",
    "null"
];

const sourceJs = fs.readFileSync(path.join(__dirname, "source.js")).toString();

async function main() {
    const tx = await contract.sendHttpayerRequest(
        parseInt(process.env.SUBSCRIPTION_ID),
        args,
        300000,
        process.env.DON_ID,
        sourceJs
    );

    console.log("Tx sent. Waiting for confirmation...");
    await tx.wait();
    console.log("Tx confirmed:", tx.hash);

    const response = await contract.s_lastResponse();
    console.log("Chainlink result:", response);
}

main().catch(console.error);
