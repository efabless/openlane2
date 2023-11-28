#!/usr/bin/env node
// Copyright 2023 Efabless Corporation
//
// Licensed under the Apache License, Version 2.0(the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

const compareMain = require("./compare_main.js");

/**
 * 
 * @param {Octokit} github 
 * @param {object} context 
 * @param {string} botUsername 
 * @param {string} body 
 */
async function postOrUpdateComment(github, context, botUsername, body) {
    const METRIC_REPORT_MARK = "<!-- MARK: METRICS REPORT -->";

    let page = 1;
    let allComments = [];
    let comments = [];
    do {
        let response = await github.request("GET /repos/{owner}/{repo}/issues/{issue_number}/comments?page={page}&per_page=100", {
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            page,
        });
        comments = response.data;
        allComments = allComments.concat(comments);
        page += 1;
    } while (comments.length != 0);

    let found = null;
    for (let comment of allComments) {
        if (comment.body.includes(METRIC_REPORT_MARK) && comment.user.login == botUsername) {
            found = comment;
            break;
        }
    }

    let fn = github.rest.issues.createComment;
    let request = {
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: `${METRIC_REPORT_MARK}\n\n${body}`
    };

    if (found) {
        request.comment_id = found.id;
        fn = github.rest.issues.updateComment;
    }

    await fn(request);
}

/**
 * 
 * @param {Octokit} github 
 * @param {object} context 
 * @param {string} botUsername 
 * @param {string} botToken 
 */
async function main(github, context, botUsername, botToken) {
    const fs = require("fs");

    let body;
    try {
        body = compareMain("ALL", "./tables_all.md", botToken);
        let tables = fs.readFileSync("./tables_all.md", { encoding: "utf8" });

        let gistResponse = await github.gists.create({
            public: true,
            description: `Results for ${context.repo.owner} / ${context.repo.repo}#${context.issue.number} (Run ${context.runId})`,
            files: {
                "10-ALL.md": {
                    content: tables
                }
            }
        });

        body += `\n\nFull tables ► ${gistResponse.data.url}\n`;
    } catch (e) {
        body = e.message;
        console.error(e.message)
    }

    await postOrUpdateComment(github, context, botUsername, body)
}

module.exports = main;

if (require.main === module) {
    // Test
    try {
        require("@octokit/rest");
    } catch (error) {
        console.error("Run 'yarn add @octokit/rest @octokit/plugin-paginate-rest'")
        process.exit(-1);
    }
    const { Octokit } = require("@octokit/rest");

    const context = {
        repo: {
            owner: "efabless",
            repo: "openlane2"
        },
        issue: {
            number: process.argv[3]
        },
        runId: "api_test"
    };

    let octokit = new Octokit({
        auth: process.argv[2],
    });

    main(octokit, context, "openlane-bot", process.argv[2]);
}