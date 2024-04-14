const { createApp, ref, toRefs, watch, shallowRef } = Vue;

const DEFAULT_MAX_DATA_POINTS = 200;

const app = createApp({
    setup() {
        const message = ref("Hello vue!");
        const search = ref("");
        const gdata = ref({});
        const pointCount = ref(DEFAULT_MAX_DATA_POINTS);
        const sources = ref([
            {
                title: "X Acceleration",
                id: "accelx",
                type: "line",
            },
            {
                title: "X Gyro",
                id: "gyrox",
                type: "line",
            },
            {
                title: "Temperature (F)",
                id: "temp",
                type: "line",
            },
            {
                title: "Log",
                id: "log",
                type: "log",
            },
            {
                title: "Altitude (ft)",
                id: "altitude",
                type: "line",
            },
        ]);
        let i = 0;

        const startWebsocket = () => {
            const ws = new WebSocket("ws://localhost:5001");
            ws.onopen = () => {
                console.log("Websocket connected");
                ws.send("Hello from client");
            };
            gdata.value["gps"] = {
                fix: false,
                satelites: 0,
                mostRecent: {
                    lat: "0",
                    lon: "0",
                },
            };
            ws.onmessage = (event) => {
                dataArray = JSON.parse(event.data);

                for (let data of dataArray) {
                    let { time, source, value } = data;
                    source = source.toLowerCase();

                    if (source == "fix") {
                        gdata.value["gps"].fix = value;
                        continue;
                    }
                    if (source == "sats") {
                        gdata.value["gps"].satelites = value;
                        continue;
                    }
                    if (source == "fixLat") {
                        gdata.value["gps"].mostRecent.lat = value;
                        continue;
                    }
                    if (source == "fixLon") {
                        gdata.value["gps"].mostRecent.lon = value;
                    }

                    if (!gdata.value[source]) {
                        gdata.value[source] = [];
                    }
                    gdata.value[source].push({ time, value });
                    if (gdata.value[source].length > pointCount.value) {
                        gdata.value.shift();
                    }
                }
                i++;
            };
        };

        startWebsocket();

        return {
            message,
            gdata,
            sources,
            search,
            pointCount,
        };
    },
});

// Components
app.component("Chart", {
    props: {
        id: String,
        data: Array,
    },
    setup(props) {
        const { id, data } = toRefs(props);

        const ctx = ref(null);
        const chart = ref(null);

        return {
            id,
            data,
            ctx,
            chart,
        };
    },
    mounted() {
        this.initChart();
        watch(this.data, () => {
            this.updateData();
        });
    },
    template: `
        <div :id="'chart-' + id" class="chart">
            <canvas :id="'chart-' + id + '-canvas'"></canvas>
        </div>
    `,
    methods: {
        initChart() {
            this.ctx = document
                .getElementById(`chart-${this.id}-canvas`)
                .getContext("2d");

            this.chart = shallowRef(
                new Chart(this.ctx, {
                    type: "line",
                    data: {
                        labels: this.data.map((d) => d.time),
                        datasets: [
                            {
                                label: "Data",
                                data: this.data.map((d) => d.value),
                                borderColor: "rgba(75, 192, 192, 1)",
                                borderWidth: 1,
                                fill: false,
                            },
                        ],
                    },
                    options: {
                        elements: {
                            point: {
                                radius: 0,
                            },
                        },
                        scales: {
                            x: {
                                type: "linear",
                                position: "bottom",
                                ticks: {
                                    callback: function (value, index, values) {
                                        return value.toFixed(2);
                                    },
                                },
                            },
                        },
                    },
                })
            );
        },
        updateData() {
            this.chart.data.labels = this.data.map((d) => d.time);
            this.chart.data.datasets[0].data = this.data.map((d) => d.value);
            this.chart.options.scales.x.min = this.data[0].time;
            this.chart.options.scales.x.max =
                this.data[this.data.length - 1].time;
            max = Math.max(...this.data.map((d) => d.value));
            min = Math.min(...this.data.map((d) => d.value));

            this.chart.options.scales.y.min = min - 0.1 * (max - min);
            this.chart.options.scales.y.max = max + 0.1 * (max - min);
            this.chart.update("none");
        },
    },
});

app.component("gps", {
    props: {
        data: Object,
    },
    setup(props) {
        const { data } = toRefs(props);

        return {
            data,
        };
    },
    template: `
        <div class="gps">
            <span :class="{'satelite-fix-indicator': true, 'fix': data.fix}"></span>
            <span class="satelite-count">{{data.satelites}} Satelites</span>
            <span class="lat-lon">{{data.mostRecent['lat']}} {{data.mostRecent['lon']}}</span>
        </div>`,
});

app.component("Log", {
    props: {
        id: String,
        data: Array,
    },
    setup(props) {
        const { id, data } = toRefs(props);

        watch(data, () => {
            const log = document.getElementById(`log-${id}`);
            log.scrollTop = log.scrollHeight;
        });

        return {
            id,
            data,
        };
    },
    template: `
        <div :id="'log-' + id" class="log">
            <ul>
                <li v-for="d in data" :key="d.time"><em class="log-time">{{ d.time.toFixed(2) }}:</em><div class="log-entry-cont"><span v-for="d2 in d.value.split('\\n').filter(l => l.length)">{{d2}}</span></div></li>
            </ul>
        </div>
    `,
});

app.component("data-wrapper", {
    props: {
        source: Object,
        data: Array,
    },
    setup(props) {
        const { source, data } = toRefs(props);

        return {
            source,
            data,
        };
    },
    template: `
        <div :id="'data-' + source?.id" class="data-cont">
            <h2 class="title">{{ source.title }}</h2>
            <div v-if="data">
                <Chart :id="source.id" :data="data" v-if="source.type=='line'" />
                <Log :id="source.id" :data="data" v-if="source.type=='log'" />
            </div>
            <div v-else>
                <em>No Data Found</em>
            </div>
        </div>
    `,
});

app.mount("#app");
