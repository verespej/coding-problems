'use strict';

const fs = require('fs');

process.stdin.resume();
process.stdin.setEncoding('utf-8');

let inputString = '';
let currentLine = 0;

process.stdin.on('data', inputStdin => {
    inputString += inputStdin;
});

process.stdin.on('end', _ => {
    inputString = inputString.trim().split('\n').map(str => str.trim());

    main();
});

function readLine() {
    return inputString[currentLine++];
}

function createContiguousSectionsRepresentation(blocksRepresentation) {
    // Ex:
    // 3, 2    -> 1, 1, 1, 2, 2
    // 2, 2, 1 -> 1, 1, 2, 2, 3
    const contigSections = new Array(blocksRepresentation.length);
    for (let i = 0; i < contigSections.length; i++) {
        contigSections[i] = [];
    }

    for (let row = 0; row < blocksRepresentation.length; row++) {
        for (let col = 0; col < blocksRepresentation[row].length; col++) {
            const sectionLength = blocksRepresentation[row][col];
            for (let segment = 0; segment < sectionLength; segment++) {
                contigSections[row].push(col);
            }
        }
    }
    return contigSections;
}

function isValidBlockSolution(blockSolution) {
    if (blockSolution.length < 1) {
        throw new Error('Invalid input: Must contain at least one entry');
    }

    const constigSections = createContiguousSectionsRepresentation(blockSolution);

    const numRows = constigSections.length;
    const numCols = constigSections[0].length;
    for (let col = 0; col < numCols - 1; col++) {
        let foundContinuity = false;
        for (let row = 0; row < numRows; row++) {
            // If there's a continuity, we don't have a
            // full vertical slice, so this column passes
            if (constigSections[row][col] === constigSections[row][col+1]) {
                foundContinuity = true;
                break;
            }
        }
        if (!foundContinuity) {
            return false;
        }
    }

    return true;
}

// Generate possibilities recursively. Root representation
// should be an array of all 1's. Recursion tree looks like:
//         1111
//  211    121    112
// 31 22  31 13  22 13
// 4  4   4   4   4  4
const MAX_BLOCK_SIZE = 4;
function getDerivativeRowPossibilities(basePossibility, visited) {
    let derivatives = [basePossibility.slice(0)];

    for (let i = 0; i < basePossibility.length - 1; i++) {
        const mergedValue = basePossibility[i] + basePossibility[i+1];
        if (mergedValue > MAX_BLOCK_SIZE) {
            continue;
        }

        const derivative = basePossibility.slice(0);
        derivative.splice(i, 2, mergedValue);

        const key = derivative.join('');
        if (visited[key]) {
            continue;
        }
        visited[key] = true;

        const subDerivatives = getDerivativeRowPossibilities(derivative, visited);
        derivatives = derivatives.concat(subDerivatives);
    }

    return derivatives;
}

function getDerivativeMatrixPossibilities(basePossibility) {
    if (basePossibility.length < 1) {
        throw new Error('Invalid input: Must contain at least one entry');
    }

    const rowPossibilities =
        getDerivativeRowPossibilities(basePossibility[0], {});

    if (basePossibility.length === 1) {
        return rowPossibilities.map(rp => [rp]);
    }

    const possibilities = [];

    const subTree =
        getDerivativeMatrixPossibilities(basePossibility.slice(1));
    for (let rpIndex = 0; rpIndex < rowPossibilities.length; rpIndex++) {
        for (let stIndex = 0; stIndex < subTree.length; stIndex++) {
            const possibility = [rowPossibilities[rpIndex]].concat(subTree[stIndex]);
            possibilities.push(possibility);
        }
    }

    return possibilities;
}

// n: height
// m: width 
function legoBlocks(n, m) {
    const baseRowPossibility = new Array(m).fill(1);
    const baseMatrixPossibility = new Array(n).fill(baseRowPossibility);
    // console.log('Base solution:');
    // console.log(baseMatrixPossibility);

    const solutions = getDerivativeMatrixPossibilities(baseMatrixPossibility);
    // console.log('Solutions:');
    // solutions.forEach(sol => console.log(sol));

    const validSolutions = solutions.filter(sol => isValidBlockSolution(sol));
    // console.log('Valid solutions:');
    // validSolutions.forEach(sol => console.log(sol));

    return validSolutions.length;
}

function main() {
    const ws = fs.createWriteStream(process.env.OUTPUT_PATH);

    const t = parseInt(readLine(), 10);

    for (let tItr = 0; tItr < t; tItr++) {
        const nm = readLine().split(' ');

        const n = parseInt(nm[0], 10);

        const m = parseInt(nm[1], 10);

        let result = legoBlocks(n, m);

        ws.write(result + "\n");
    }

    ws.end();
}
